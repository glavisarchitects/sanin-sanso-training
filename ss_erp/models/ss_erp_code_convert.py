# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CodeConvert(models.Model):
    _name = 'ss_erp.code.convert'
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

    # @api.depends('convert_code_type')
    # def _compute_resource_ref(self):
    #     for line in self:
    #         if line.convert_code_type:
    #             value = line.value or ''
    #             try:
    #                 value = int(value)
    #                 if not self.env[line.convert_code_type.model.model].search([('id', '=', value)]):
    #                     record = list(self.env[line.convert_code_type.model.model]._search([], limit=1))
    #                     value = record[0] if record else 0
    #             except ValueError:
    #                 record = list(self.env[line.convert_code_type.model.model]._search([], limit=1))
    #                 value = record[0] if record else 0
    #             line.internal_code = '%s,%s' % (line.convert_code_type.model.model, value)
    #         else:
    #             line.internal_code = False
    #
    # @api.onchange('internal_code')
    # def _set_resource_ref(self):
    #     for line in self:
    #         if line.internal_code:
    #             line.value = str(line.internal_code.id)

    @api.onchange('convert_code_type')
    def _onchange_convert_code_type(self):
        if self.convert_code_type:
            record = list(self.env[self.convert_code_type.model.model]._search([], limit=1))
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
