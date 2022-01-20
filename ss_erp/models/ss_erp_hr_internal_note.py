# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrInternalNote(models.Model):
    _name = "ss_erp.hr.internal.note"

    organization_id = fields.Many2one('ss_erp.organization', string='組織名')
    name = fields.Char('メモ')
    ref = fields.Many2many('hr.expense.sheet', string='参照元')

    @api.onchange('organization_id')
    def onchange_organization_id(self):
        if self.organization_id:
            self.ref = self.env['hr.expense.sheet'].search([('x_organization_id', 'in', self.organization_id.ids)])


