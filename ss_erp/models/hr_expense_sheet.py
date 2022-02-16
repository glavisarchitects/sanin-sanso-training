# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    x_sub_account_id = fields.Many2one('ss_erp.account.subaccount', string='補助科目')
    x_request_date = fields.Date(string='申請日')
    x_organization_id = fields.Many2one('ss_erp.organization', string='申請組織',default=lambda self: self._get_default_x_organization_id())
    x_responsible_id = fields.Many2one('ss_erp.responsible.department', string='申請部署',default=lambda self: self._get_default_x_responsible_dept_id())

    @api.onchange('account_id')
    def onchange_sub_account_id(self):
        if self.account_id:
            sub_accounts = self.account_id.x_sub_account_ids.ids
            return {'domain': {'x_sub_account_id': [('id', 'in', sub_accounts)]
                               }}

    def _get_default_x_organization_id(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id.organization_first
        else:
            return False

    def _get_default_x_responsible_dept_id(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id.department_jurisdiction_first[0]
        else:
            return False