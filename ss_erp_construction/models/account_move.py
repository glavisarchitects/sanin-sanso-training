# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_construction_order_id = fields.Many2one('ss.erp.construction', string='工事オーダ')
    invoice_type = fields.Char()

    def _recompute_payment_terms_lines(self):
        super()._recompute_payment_terms_lines()
        if self.journal_id.is_construction:
            if self.is_sale_document(include_receipts=True) and self.partner_id:
                new_term_account = self.partner_id.x_construction_account_receivable_id
            elif self.is_purchase_document(include_receipts=True) and self.partner_id:
                new_term_account = self.partner_id.x_construction_account_payable_id
            else:
                new_term_account = None
            for line in self.line_ids:
                line.partner_id = self.partner_id

                if new_term_account and line.account_id.user_type_id.type in ('receivable', 'payable'):
                    line.account_id = new_term_account


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    construction_line_ids = fields.Many2many(
        'ss.erp.construction.component',
        'construction_order_line_invoice_rel',
        'invoice_line_id', 'order_line_id',
        string='工事明細', readonly=True, copy=False)

    def _get_computed_account(self):
        self.ensure_one()
        self = self.with_company(self.move_id.journal_id.company_id)

        if not self.product_id:
            return

        if not self.move_id.x_construction_order_id:
            return super()._get_computed_account()
        else:

            fiscal_position = self.move_id.fiscal_position_id
            accounts = self.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
            if self.move_id.is_sale_document(include_receipts=True):
                # Out invoice.
                return accounts['construction_income'] or accounts['income']
            elif self.move_id.is_purchase_document(include_receipts=True):
                # In invoice.
                return accounts['construction_expense'] or accounts['expense']
