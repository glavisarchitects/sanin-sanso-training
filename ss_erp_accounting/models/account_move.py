# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_organization_id = fields.Many2one(
        'ss_erp.organization', string="担当組織", index=True,
        default=lambda self: self._get_default_x_organization_id())
    x_responsible_dept_id = fields.Many2one(
        'ss_erp.responsible.department', string="管轄部門", index=True,
        default=lambda self: self._get_default_x_responsible_dept_id())

    def _get_default_x_organization_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id.organization_first
        else:
            return False

    def _get_default_x_responsible_dept_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id and employee_id.department_jurisdiction_first:
            return employee_id.department_jurisdiction_first[0]
        else:
            return False

    x_responsible_user_id = fields.Many2one('res.users', string='業務担当')
    x_mkt_user_id = fields.Many2one('res.users', string='営業担当')
    x_is_fb_created = fields.Boolean(string='FB作成済みフラグ', store=True, default=False, copy=False)
    x_is_not_create_fb = fields.Boolean(string='FB対象外', store=True, index=True)

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
        required=False, index=True, store=True)

    x_payment_type = fields.Selection(
        string='支払手段',
        selection=[('bank', '振込'),
                   ('cash', '現金'),
                   ('bills', '手形'), ],
        required=False, index=True, store=True)

    def _move_autocomplete_invoice_lines_values(self):
        ''' This method recomputes dynamic lines on the current journal entry that include taxes, cash rounding
        and payment terms lines.
        '''
        self.ensure_one()

        for line in self.line_ids.filtered(lambda l: not l.display_type):
            analytic_account = line._cache.get('analytic_account_id')

            # Do something only on invoice lines.
            if line.exclude_from_invoice_tab:
                continue

            # Shortcut to load the demo data.
            # Doing line.account_id triggers a default_get(['account_id']) that could returns a result.
            # A section / note must not have an account_id set.
            if not line._cache.get('account_id') and not line._origin:
                line.account_id = line._get_computed_account() or self.journal_id.default_account_id

            line.x_sub_account_id = line.account_id.x_sub_account_ids[0] if line.account_id.x_sub_account_ids else False

            if line.product_id and not line._cache.get('name'):
                line.name = line._get_computed_name()

            # Compute the account before the partner_id
            # In case account_followup is installed
            # Setting the partner will get the account_id in cache
            # If the account_id is not in cache, it will trigger the default value
            # Which is wrong in some case
            # It's better to set the account_id before the partner_id
            # Ensure related fields are well copied.
            if line.partner_id != self.partner_id.commercial_partner_id:
                line.partner_id = self.partner_id.commercial_partner_id
            line.date = self.date
            line.recompute_tax_line = True
            line.currency_id = self.currency_id
            if analytic_account:
                line.analytic_account_id = analytic_account

        self.line_ids._onchange_price_subtotal()
        self._recompute_dynamic_lines(recompute_all_taxes=True)

        values = self._convert_to_write(self._cache)
        values.pop('invoice_line_ids', None)
        return values

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        approval_account_move_in = self.env['approval.request'].search([('x_account_move_ids', 'in', self.id),
                                                                        ('request_status', 'not in',
                                                                         ['cancel', 'refuse'])])
        if approval_account_move_in and self.move_type == 'in_invoice':
            for approval in approval_account_move_in:
                if len(approval.x_account_move_ids) > 1:
                    message = '仕入請求伝票%sが見積操作で取消されたため、承認申請から削除されました。' % self.name
                    approval.sudo().write({'x_account_move_ids': [(3, self.id)]})
                    approval.message_post(body=message)
                else:
                    approval.sudo().update({
                        'request_status': 'cancel',
                    })
                    approval.message_post(body=_('承認申請の仕入請求伝票が仕入請求操作で取消されたため、承認申請を取消しました。'))
        return res

    def action_register_payment(self):
        res = super().action_register_payment()
        res['context']['default_x_organization_id'] = self.x_organization_id.id
        res['context']['default_x_responsible_dept_id'] = self.x_responsible_dept_id.id
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def default_x_sub_account_id(self):
        if self.account_id and self.account_id.x_sub_account_ids and self.move_id.journal_id.default_account_id == self.account_id:
            return self.account_id.x_sub_account_ids[0]

    x_sub_account_id = fields.Many2one('ss_erp.account.subaccount', string='補助科目', default=default_x_sub_account_id)
    x_sub_account_ids = fields.Many2many('ss_erp.account.subaccount', related='account_id.x_sub_account_ids')

    x_organization_id = fields.Many2one('ss_erp.organization', related='move_id.x_organization_id')
    x_responsible_dept_id = fields.Many2one('ss_erp.responsible.department', related='move_id.x_responsible_dept_id')

    @api.onchange('account_id')
    def _onchange_get_x_sub_account(self):
        journal_item_match = self.move_id.line_ids.filtered(lambda l: l.account_id == self.account_id.id)
        if self.account_id and self.account_id.x_sub_account_ids and self.move_id.journal_id.default_account_id == self.account_id:
            self.x_sub_account_id = self.account_id.x_sub_account_ids[0]
            journal_item_match.x_sub_account_id = self.account_id.x_sub_account_ids[0]
        else:
            self.x_sub_account_id = False
            journal_item_match.x_sub_account_id = False
