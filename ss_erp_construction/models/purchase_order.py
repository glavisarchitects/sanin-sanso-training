# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_round
from odoo.tools import float_is_zero, float_compare
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)
from itertools import groupby


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_construction_order_id = fields.Many2one('ss.erp.construction', string='工事オーダ')

    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res.update({
            'x_construction_order_id': self.x_construction_order_id and self.x_construction_order_id.id or False,
        })
        return res

    @api.model
    def _prepare_down_payment_section_line(self, **optional_values):
        """
        Prepare the dict of values to create a new down payment section for a construction order line.

        :param optional_values: any parameter that should be added to the returned down payment section
        """
        down_payments_section_line = {
            'display_type': 'line_section',
            'name': _('前払金'),
            'product_id': False,
            'product_uom_id': False,
            'quantity': 0,
            'discount': 0,
            'price_unit': 0,
            'account_id': False
        }
        if optional_values:
            down_payments_section_line.update(optional_values)
        return down_payments_section_line

    @api.model
    def _nothing_to_invoice_error(self):
        msg = _("""請求するものは何もありません！""")
        return UserError(msg)

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        invoice_vals.update({
            'x_organization_id': self.x_organization_id.id,
            'x_responsible_dept_id': self.x_responsible_dept_id.id,
        })
        if self.x_bis_categ_id == 'gas_material':
            invoice_vals.update({
                'invoice_type': 'gas_material'
            })
        else:

            self.ensure_one()
            journal = self.env['account.journal'].sudo().search(
                [('type', '=', 'purchase'), ('x_is_construction', '=', True)],
                limit=1)
            if not journal:
                raise UserError('工事購買の仕訳帳は設定していません。もう一度ご確認ください')
            invoice_vals.update({
                'journal_id': journal.id,
                'invoice_type': 'construction'
            })
        return invoice_vals

    def _get_invoiceable_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        down_payment_line_ids = []
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for line in self.order_line:
            if line.display_type == 'line_section':
                # Only invoice the section if one of its lines is invoiceable
                pending_section = line
                continue
            if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
                continue
            if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
                if line.is_downpayment:
                    # Keep down payment lines separately, to put them together
                    # at the end of the invoice, in a specific dedicated section.
                    down_payment_line_ids.append(line.id)
                    continue
                if pending_section:
                    invoiceable_line_ids.append(pending_section.id)
                    pending_section = None
                invoiceable_line_ids.append(line.id)

        return self.env['purchase.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)

    def _create_invoices(self, final=False):
        """
        Create the invoice associated to the Construction Order.
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        invoice_vals_list = []
        invoice_item_sequence = 0  # Incremental sequencing to keep the lines order on the invoice.

        for order in self:
            if order.invoice_status != 'to invoice':
                continue

            order = order.with_company(order.company_id)
            pending_section = None

            invoice_vals = order._prepare_invoice()
            invoiceable_lines = order._get_invoiceable_lines(final)

            invoice_line_vals = []
            down_payment_section_added = False
            for line in invoiceable_lines:
                if not down_payment_section_added and line.is_downpayment:
                    # Create a dedicated section for the down payments
                    # (put at the end of the invoiceable_lines)
                    invoice_line_vals.append(
                        (0, 0, self._prepare_down_payment_section_line(
                            sequence=invoice_item_sequence,
                        )),
                    )
                    down_payment_section_added = True
                    invoice_item_sequence += 1

                line_vals = line._prepare_account_move_line()
                line_vals.update({'sequence': invoice_item_sequence})
                invoice_line_vals.append(
                    (0, 0, line_vals),
                )
                invoice_item_sequence += 1

            if invoice_line_vals is not None:
                invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise self._nothing_to_invoice_error()

        new_invoice_vals_list = []
        for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (
            x.get('company_id'), x.get('partner_id'), x.get('currency_id'), x.get('invoice_type'))):
            origins = set()
            payment_refs = set()
            refs = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
                payment_refs.add(invoice_vals['payment_reference'])
                refs.add(invoice_vals['ref'])
            ref_invoice_vals.update({
                'ref': ', '.join(refs)[:2000],
                'invoice_origin': ', '.join(origins),
                'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
            })
            new_invoice_vals_list.append(ref_invoice_vals)

        invoice_vals_list = []

        for ele in new_invoice_vals_list:
            del ele['invoice_type']
            invoice_vals_list.append(ele)
        # invoice_vals_list = new_invoice_vals_list

        moves = self.env['account.move'].sudo().with_context(default_move_type='in_invoice').create(
            invoice_vals_list)

        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        return moves


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    is_downpayment = fields.Boolean(
        string="頭金であるか", help="Down payments are made when creating invoices from a construction order.")

    construction_line = fields.Many2many('ss.erp.construction.component', 'construction_order_line_purchase_order_line_rel','po_line_id',
                                            'order_line_id'
                                            , string='購買明細', copy=False)
