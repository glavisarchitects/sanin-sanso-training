# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    x_sub_account_id = fields.Many2one('ss_erp.account.subaccount', string='補助科目')
    x_request_date = fields.Date(string='申請日')
    x_organization_id = fields.Many2one('ss_erp.organization', string='申請組織',default=lambda self: self._get_default_x_organization_id())
    x_responsible_id = fields.Many2one('ss_erp.responsible.department', string='申請部署',default=lambda self: self._get_default_x_responsible_dept_id())
    x_sub_account_related_ids = fields.Many2many(related='account_id.x_sub_account_ids')

    @api.onchange('account_id')
    def onchange_sub_account_id(self):
        if self.account_id:
            sub_accounts = self.account_id.x_sub_account_ids.ids
            return {'domain': {'x_sub_account_id': [('id', 'in', sub_accounts)]
                               }}


    def _create_sheet_from_expenses(self):
        res = super(HrExpense, self)._create_sheet_from_expenses()
        res.update({
            'x_request_date': self.x_request_date,
            'x_organization_id': self.x_organization_id.id,
            'x_responsible_id': self.x_responsible_id.id,
        })
        return res

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

    def write(self, vals):
        res = super(HrExpense, self).write(vals)
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if self.x_organization_id not in employee_id.organization_first:
            raise UserError('申請者の所属組織を選択してください')
        if self.x_responsible_id not in employee_id.department_jurisdiction_first :
            raise UserError(_('申請者の所属部署を選択してください'))
        return res