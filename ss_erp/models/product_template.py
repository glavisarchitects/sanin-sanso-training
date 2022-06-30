# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_fixed_cost = fields.Float("仕入定価", default=0, tracking=True)
    x_supply_fixed_cost = fields.Float("仕入定価", default=0, tracking=True)
    x_product_unit_measure_ids = fields.One2many('ss_erp.product.units.measure',"product_template_id",string='代替単位', tracking=True)
    x_product_unit_measure_id = fields.Many2one('ss_erp.product.units.measure', '代替単位ID', tracking=True)
    x_alternative_uom_id = fields.Many2one(related='x_product_unit_measure_id.alternative_uom_id', string='代替単位', tracking=True)
    x_converted_value = fields.Float(related='x_product_unit_measure_id.converted_value', string='換算値', tracking=True)
    x_remarks = fields.Char(related='x_product_unit_measure_id.remarks', string='換算値', tracking=True)

    x_major_classification_id = fields.Many2one('ss_erp.product.major.classification', string='プロダクト大分類',store=True, tracking=True)
    x_medium_classification_id = fields.Many2one('ss_erp.product.medium.classification', string='プロダクト中分類',store=True, tracking=True)
    x_minor_classification_id = fields.Many2one('ss_erp.product.minor.classification', string='プロダクト小分類',store=True, tracking=True)
    x_detail_classification_id = fields.Many2one('ss_erp.product.detail.classification',string='プロダクト詳細分類', tracking=True)

    def write(self, vals):
        update_product_template = True
        if vals.get('source'):
            vals.pop('source')
            update_product_template = False
        res = super(ProductTemplate, self).write(vals)
        if update_product_template and len(vals) > 0 and self._name != 'ss_erp.product.template.form':
            values = {}
            form_id = self.env['ss_erp.product.template.form'].search([('product_template_id', '=', self.id)])
            values.update({'source': 'product_template'})
            for field_name, field_value in vals.items():
                if type(self._fields[field_name].compute) != str:
                    if self._fields[field_name].type in ['one2many', 'many2many']:
                        value = getattr(self, field_name, ())
                        value = [(6, 0, value.ids)] if value else False
                    else:
                        value = getattr(self, field_name)
                        if self._fields[field_name].type == 'many2one':
                            value = value.id if value else False
                values.update({field_name: value})
            form_id.write(values)
        return res

    def _create_variant_ids(self):
        if self._name == 'ss_erp.product.template.form':
            return True
        return super(ProductTemplate, self)._create_variant_ids()