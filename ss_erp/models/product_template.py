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

    x_major_classification_id = fields.Many2one('ss_erp.product.major.classification', string='プロダクト大分類名称',store=True, tracking=True)
    x_medium_classification_id = fields.Many2one('ss_erp.product.medium.classification', string='プロダクト中分類名称',store=True, tracking=True)
    x_minor_classification_id = fields.Many2one('ss_erp.product.minor.classification', string='プロダクト小分類名称',store=True, tracking=True)
    x_detail_classification_id = fields.Many2one('ss_erp.product.detail.classification',string='プロダクト詳細分類名称', tracking=True)

    x_major_classification_code = fields.Char(related='x_major_classification_id.major_classification_code',string='プロダクト大分類')
    x_medium_classification_code = fields.Char(related='x_medium_classification_id.medium_classification_code',string='プロダクト中分類')
    x_minor_classification_code = fields.Char(related='x_minor_classification_id.minor_classification_code',string='プロダクト小分類')
    x_detail_classification_code = fields.Char(related='x_detail_classification_id.detail_classification_code',string='プロダクト詳細分類')

    # @api.onchange('x_detail_classification_id')
    # def _onchange_x_detail_classification_id(self):
    #     if self.x_detail_classification_code:
    #         self.x_minor_classification_id = self.x_detail_classification_id.minor_classification_code.id
    #         self.x_medium_classification_id = self.x_minor_classification_id.medium_classification_code.id
    #         self.x_major_classification_id = self.x_medium_classification_id.major_classification_code.id
