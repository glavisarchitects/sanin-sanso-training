# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ConstructionAdvancePaymentInv(models.TransientModel):
    _name = "ss_erp.construction.advance.payment.inv"
    _description = "Construction Advance Payment Invoice"

    @api.model
    def _count(self):
        return len(self._context.get('active_ids', []))

    @api.model
    def _default_product_id(self):
        product_id = self.env.ref("ss_erp_product_template.down_payment_product_product_data")
        return product_id

    @api.model
    def _default_deposit_account_id(self):
        return self._default_product_id()._get_product_accounts()['income']

    @api.model
    def _default_deposit_taxes_id(self):
        return self._default_product_id().taxes_id

    @api.model
    def _default_has_down_payment(self):
        if self._context.get('active_model') == 'ss.erp.construction' and self._context.get('active_id', False):
            construction_order = self.env['ss.erp.construction'].browse(self._context.get('active_id'))
            return construction_order.construction_component_ids.filtered(lambda line: line.is_downpayment)
        return False

    @api.model
    def _default_currency_id(self):
        if self._context.get('active_model') == 'ss.erp.construction' and self._context.get('active_id', False):
            construction_order = self.env['ss.erp.construction'].browse(self._context.get('active_id'))
            return construction_order.currency_id

    advance_payment_method = fields.Selection([
        ('delivered', '通常の請求書'),
        ('percentage', '前受金 (パーセント)'),
        ('fixed', '前受金 (固定金額)')
    ], string='請求書作成', default='delivered', required=True, )
    deduct_down_payments = fields.Boolean('頭金を差し引く', default=True)
    has_down_payments = fields.Boolean('頭金がある', default=_default_has_down_payment, readonly=True)
    product_id = fields.Many2one('product.product', string='前受金', domain=[('type', '=', 'service')],
                                 default=_default_product_id)
    amount = fields.Float('前受金額', digits='Account', help="事前に請求される金額の割合。税金は含まれていません。")
    currency_id = fields.Many2one('res.currency', string='通貨', default=_default_currency_id)
    fixed_amount = fields.Monetary('頭金(固定)', help="事前に請求される定額(税抜き)。")
    deposit_account_id = fields.Many2one("account.account", string="収益勘定", domain=[('deprecated', '=', False)],
                                         help="預金用口座", default=_default_deposit_account_id)
    deposit_taxes_id = fields.Many2many("account.tax", string="顧客税", help="預金に使用される税金",
                                        default=_default_deposit_taxes_id)
    count = fields.Integer(default=_count, string='Order Count')

    @api.onchange('advance_payment_method')
    def onchange_advance_payment_method(self):
        if self.advance_payment_method == 'percentage':
            amount = self.default_get(['amount']).get('amount')
            return {'value': {'amount': amount}}
        return {}

    def _prepare_invoice_values(self, order, name, amount, order_line):
        invoice_vals = {
            'ref': order.client_order_ref,
            'move_type': 'out_invoice',
            'invoice_origin': order.name,
            'x_organization_id': order.organization_id.id,
            'x_responsible_dept_id': order.responsible_dept_id.id,
            'x_construction_order_id': order.id,
            'invoice_user_id': order.user_id.id,
            'partner_id': order.partner_id.id,
            'fiscal_position_id': (order.fiscal_position_id or order.fiscal_position_id.get_fiscal_position(
                order.partner_id.id)).id,
            'partner_shipping_id': order.partner_id.id,
            'currency_id': order.currency_id.id,
            'invoice_payment_term_id': order.payment_term_id.id,
            'partner_bank_id': order.partner_id.bank_ids[:1].id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'price_unit': amount,
                'quantity': 1.0,
                'product_id': self.product_id.id,
                'product_uom_id': order_line.product_uom_id.id,
                'tax_ids': [(6, 0, order_line.tax_id.ids)],
            })],
        }

        return invoice_vals

    def _get_advance_details(self, order):
        context = {'lang': order.partner_id.lang}
        if self.advance_payment_method == 'percentage':
            if all(self.product_id.taxes_id.mapped('price_include')):
                amount = order.amount_total * self.amount / 100
            else:
                amount = order.amount_untaxed * self.amount / 100
            name = _("%s%% の前受金") % (self.amount)
        else:
            amount = self.fixed_amount
            name = _('前受金')
        del context

        return amount, name

    def _create_invoice(self, order, order_line, amount):
        if (self.advance_payment_method == 'percentage' and self.amount <= 0.00) or (
                self.advance_payment_method == 'fixed' and self.fixed_amount <= 0.00):
            raise UserError(_('前受金の金額は正の値でなければなりません。'))

        amount, name = self._get_advance_details(order)

        invoice_vals = self._prepare_invoice_values(order, name, amount, order_line)

        if order.fiscal_position_id:
            invoice_vals['fiscal_position_id'] = order.fiscal_position_id.id

        invoice = self.env['account.move'].with_company(order.company_id) \
            .sudo().create(invoice_vals).with_user(self.env.uid)
        return invoice

    def _prepare_construction_component(self, order, tax_ids, amount):
        context = {'lang': order.partner_id.lang}
        construction_component_values = {
            'name': _('前受金: %s') % (time.strftime('%m %Y'),),
            'sale_price': amount,
            'product_uom_qty': 0.0,
            'construction_id': order.id,
            'product_uom_id': self.product_id.uom_id.id,
            'product_id': self.product_id.id,
            'tax_id': [(6, 0, tax_ids)] if tax_ids else False ,
            'is_downpayment': True,
        }
        del context
        return construction_component_values

    def create_invoices(self):
        construction_order_ids = self.env['ss.erp.construction'].browse(self._context.get('active_ids', []))

        if self.advance_payment_method == 'delivered':
            construction_order_ids._create_invoices(final=self.deduct_down_payments)
        else:

            construction_component_obj = self.env['ss.erp.construction.component']
            for construction_order in construction_order_ids:
                amount, name = self._get_advance_details(construction_order)

                taxes = self.product_id.taxes_id.filtered(
                    lambda r: not construction_order.company_id or r.company_id == construction_order.company_id)
                tax_ids = construction_order.fiscal_position_id.map_tax(taxes, self.product_id,
                                                                        construction_order.partner_id).ids
                construction_component_values = self._prepare_construction_component(construction_order, tax_ids, amount)
                construction_component = construction_component_obj.create(construction_component_values)
                self._create_invoice(construction_order, construction_component, amount)
        if self._context.get('open_invoices', False):
            return construction_order_ids.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}
