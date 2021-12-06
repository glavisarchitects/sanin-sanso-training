# -*- coding: utf-8 -*-
from odoo import models, api, fields


class ConvertCodeType(models.Model):
    _name = 'ss_erp.convert.code.type'
    _description = 'Convert Code Type'

    name = fields.Char(
        string='Conversion code type name', index=True, required=True, copy=False)
    code = fields.Char(string='Code', index=True, required=True, copy=False)
    model = fields.Many2one(
        'ir.model', string='Model', required=True, ondelete="cascade", copy=False)
    fields = fields.Many2one(
        'ir.model.fields', string='Item', required=True,
        ondelete='cascade', domain="[('model_id', '=', model)]", copy=False)

    @api.onchange('model')
    def onchange_model(self):
        self.fields = False

    def write(self, values):
        res = super(ConvertCodeType, self).write(values)
        code_convert = self.env['ss_erp.code.convert'].search([('convert_code_type', '=', self.id)])
        if values.get('model') and code_convert:
            raise UserError(_('Convert code type for being used for covert code')%(self.model.name))
        return res