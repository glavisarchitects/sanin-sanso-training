# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class CodeConvert(models.Model):
    _name = 'ss_erp.code.convert'
    _description = 'Code Convert'
    _rec_name = 'external_system'


    @api.model
    def _selection_target_model(self):
        return [(model.model, model.name) for model in self.env['ir.model'].search([])]

    external_system = fields.Many2one('ss_erp.external.system.type', string='External system', required=True, copy=False)
    convert_code_type = fields.Many2one('ss_erp.convert.code.type', string='Conversion code type', required=True, copy=False)
    external_code = fields.Char(string='External')
    priority_conversion = fields.Boolean(string='Priority conversion destination', required=True, default=False, copy=False)
    internal_code = fields.Reference(selection='_selection_target_model', inverse='_set_resource_ref', compute='_compute_resource_ref', copy=False)
    value = fields.Text(required=True, help="Expression containing a value specification. \n"
                                            "When Formula type is selected, this field may be a Python expression "
                                            " that can use the same values as for the code field on the server action.\n"
                                            "If Value type is selected, the value will be used directly without evaluation.")
    active = fields.Boolean(string='Active', default=True)
    _sql_constraints = [('unique_convert_code', 'unique(external_system, convert_code_type, external_code)', _('The input code conversion definition has already been registered'))	]

    @api.depends('convert_code_type')
    def _compute_resource_ref(self):
        for line in self:
            if line.convert_code_type:
                value = line.value or ''
                try:
                    value = int(value)
                    if not self.env[line.convert_code_type.model.model].search([('id', '=', value)]):
                        record = list(self.env[line.convert_code_type.model.model]._search([], limit=1))
                        value = record[0] if record else 0
                except ValueError:
                    record = list(self.env[line.convert_code_type.model.model]._search([], limit=1))
                    value = record[0] if record else 0
                line.internal_code = '%s,%s' % (line.convert_code_type.model.model, value)
            else:
                line.internal_code = False

    @api.onchange('internal_code')
    def _set_resource_ref(self):
        for line in self:
            if line.internal_code:
                line.value = str(line.internal_code.id)

