# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrInternalNote(models.Model):
    _name = "ss_erp.hr.internal.note"
    _description = "支店入出金ノート"

    organization_id = fields.Many2one('ss_erp.organization', string='組織名', index=True)
    name = fields.Char('メモ')
    ref = fields.Many2many('hr.expense.sheet', string='参照元')





