# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CodeConvert(models.Model):
    _name = 'ss_erp.code.convert'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Code Convert'
    _rec_name = 'external_system'

    @api.model
    def _selection_target_model(self):
        return [(model.model, model.name) for model in self.env['ir.model'].search([])]

    external_system = fields.Many2one('ss_erp.external.system.type', string='External system', required=True)
    convert_code_type = fields.Many2one('ss_erp.convert.code.type', string='Conversion code type', required=True)
    external_code = fields.Char(string='External')
    priority_conversion = fields.Boolean(string='Priority conversion destination', required=True, default=False)
    internal_code = fields.Reference(selection='_selection_target_model', store=True)
    value = fields.Text(required=False)
    active = fields.Boolean(default=True, )

    @api.onchange('convert_code_type')
    def _onchange_convert_code_type(self):
        if self.convert_code_type:
            record = list(self.env[self.convert_code_type.model.model].search([], limit=1))
            value = record[0] if record else 0
            if value:
                self.internal_code = '%s,%s' % (self.convert_code_type.model.model, value)
            else:
                self.internal_code = False

    @api.constrains('external_system', 'convert_code_type', 'external_code')
    def _check_model(self):
        for record in self:
            convert_code_type = self.search([('external_system', '=', record.external_system.id),
                                             ('convert_code_type', '=', record.convert_code_type.id),
                                             ('external_code', '=', record.external_code), ('id', '!=', record.id)])
            if convert_code_type:
                raise ValidationError(_('A Code Convert already exists!'))
