# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round, float_is_zero


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    _description = 'Register Payment'

    x_sub_account_id = fields.Many2one('ss_erp.account.subaccount', store=True, string='補助科目')
    x_total_fraction = fields.Monetary(compute='_compute_total_fraction', string='端数会計額')
    x_line_ids = fields.One2many('ss_erp.post.difference.account', 'acc_payment_register_id',
                                 string="Journal items")

    x_journal_sub_account = fields.Many2many('ss_erp.account.subaccount', compute='_compute_x_journal_sub_account')

    x_organization_id = fields.Many2one(
        'ss_erp.organization', string="担当組織", index=True)
    x_responsible_dept_id = fields.Many2one(
        'ss_erp.responsible.department', string="管轄部門", index=True)

    x_payment_type = fields.Selection(
        string='支払手段',
        selection=[('bank', '振込'),
                   ('cash', '現金'),
                   ('bills', '手形'), ],
        required=False, )

    x_receipt_type = fields.Selection(
        string='入金手段',
        selection=[
            ('bank', '振込'),
            ('transfer', '振替'),
            ('bills', '手形'),
            ('cash', '現金'),
            ('paycheck', '小切手'),
            ('branch_receipt', '他店入金'),
            ('offset', '相殺'), ],
        required=False, )


    # -------------------------------------------------------------------------
    # BUSINESS METHODS
    # -------------------------------------------------------------------------
    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        line_payment = []
        for rec in self.x_line_ids:
            values = {
                'account_id': rec.writeoff_account_id.id,
                'name': rec.writeoff_label,
                'amount': rec.payment_money
            }
            # line_payment.append((0, 0, values))
            line_payment.append(values)
        payment_vals['write_off_line_vals'] = line_payment
        payment_vals['x_sub_account_id'] = self.x_sub_account_id.id
        payment_vals['x_organization_id'] = self.x_organization_id.id
        payment_vals['x_responsible_dept_id'] = self.x_responsible_dept_id.id
        payment_vals['x_receipt_type'] = self.x_receipt_type
        payment_vals['x_payment_type'] = self.x_payment_type

        return payment_vals

    @api.depends('journal_id')
    def _compute_x_journal_sub_account(self):
        for rec in self:
            rec.x_journal_sub_account = False
            if rec.journal_id and rec.journal_id.default_account_id:
                if rec.journal_id.default_account_id.x_sub_account_ids:
                    rec.x_journal_sub_account = rec.journal_id.default_account_id.x_sub_account_ids

    @api.onchange('journal_id')
    def _get_default_x_sub_account(self):
        self.x_sub_account_id = False
        if self.journal_id and self.journal_id.default_account_id:
            if self.journal_id.default_account_id.x_sub_account_ids:
                self.x_sub_account_id = self.journal_id.default_account_id.x_sub_account_ids[0]

    @api.onchange('x_line_ids')
    def _compute_total_fraction(self):
        for item in self:
            item.x_total_fraction = (sum(self.x_line_ids.mapped('payment_money')))

    def action_create_payments(self):
        for rec in self:
            if rec.payment_difference and rec.payment_difference_handling == 'reconcile':
                if rec.payment_difference != rec.x_total_fraction:
                    raise UserError(_('支払差額と端数合計額が一致しないため、消込はできません。支払差額を確認し、正しく入力してください。'))
        return super().action_create_payments()
