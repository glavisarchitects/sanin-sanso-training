# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ConvertCodeType(models.Model):
    _name = 'ss_erp.convert.code.type'
    _description = 'Convert Code Type'

    name = fields.Char('Conversion code type name', index=True, required=True)
    code = fields.Char(string='Code', index=True, required=True)
    model = fields.Many2one('ir.model', string='Model', required=True, ondelete="cascade",)
    fields = fields.Many2one('ir.model.fields', string='Item', required=True, ondelete='cascade')

    @api.onchange('model')
    def _onchange_model(self):
        if self.model:
            return {'domain': {'fields':[('model_id', '=', self.model.id)]}}