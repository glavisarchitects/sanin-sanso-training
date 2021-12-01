# -*- coding: utf-8 -*-
from odoo import models, api, fields


class ConvertCodeType(models.Model):
    _name = 'ss_erp.convert.code.type'
    _description = 'Convert Code Type'

    name = fields.Char(
        string='Conversion code type name', index=True, required=True)
    code = fields.Char(string='Code', index=True, required=True)
    model = fields.Many2one(
        'ir.model', string='Model', required=True, ondelete="cascade", )
    fields = fields.Many2one(
        'ir.model.fields', string='Item', required=True,
        ondelete='cascade', domain="[('model_id', '=', model)]")