# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class ConvertCodeType(models.Model):
    _name = 'ss_erp.convert.code.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Convert Code Type'

    name = fields.Char(
        string='Conversion code type name', index=True, required=True, copy=False)
    code = fields.Char(string='Code', index=True, required=True, copy=False)
    model = fields.Many2one(
        'ir.model', string='Model', required=True, ondelete="cascade", copy=False )
    fields = fields.Many2one(
        'ir.model.fields', string='Item', required=True,
        ondelete='cascade', domain="[('model_id', '=', model)]", copy=False)

    _sql_constraints = [('unique_convert_code_type', 'unique(name, code, model, fields)', _('The input code conversion definition has already been registered'))	]

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        res = super(ConvertCodeType, self).copy(default)
        return res

    @api.onchange('model')
    def onchange_model(self):
        if self.model:
            if self.fields and self.fields.model_id != self.model:
                self.fields = False

    @api.constrains('model')
    def _check_model(self):
        for type in self:
            convert_code = self.env['ss_erp.code.convert'].search([('convert_code_type', '=', type.id)])
            if convert_code:
                raise ValidationError(_('A Convert Code Type was used.'))
