# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrInternalNote(models.Model):
    _name = "ss_erp.hr.internal.note"
    _description = "支店入出金ノート"

    organization_id = fields.Many2one('ss_erp.organization', string='組織名', index=True,default=lambda self: self._get_default_x_organization_id())
    name = fields.Char('メモ')
    ref = fields.Many2many('hr.expense.sheet', string='参照元')

    def _get_default_x_organization_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id.organization_first
        else:
            return False



