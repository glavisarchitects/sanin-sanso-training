# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_fixed_cost = fields.Float("仕入定価", default=0)
    x_supply_fixed_cost = fields.Float("仕入定価", default=0)
    product_unit_measure_ids = fields.One2many('ss_erp.product.units.measure',
                                                "product_id",
                                                string='代替単位')
    product_unit_measure_id = fields.Many2one('ss_erp.product.units.measure', '代替単位ID')
    alternative_uom_id = fields.Char(related='product_unit_measure_id.alternative_uom_id', string='代替単位')
    converted_value = fields.Float(related='product_unit_measure_id.converted_value', string='換算値')
    remarks = fields.Char(related='product_unit_measure_id.remarks', string='換算値')

    major_classification_id = fields.Many2one('ss_erp.product.major.classification', string='プロダクト大分類名称')
    medium_classification_id = fields.Many2one('ss_erp.product.medium.classification', string='プロダクト中分類名称')
    minor_classification_id = fields.Many2one('ss_erp.product.minor.classification', string='プロダクト小分類名称')
    detail_classification_id = fields.Many2one('ss_erp.product.detail.classification',string='プロダクト詳細分類名称')

    major_classification_code = fields.Char(related='major_classification_id.major_classification_code',string='プロダクト大分類')
    medium_classification_code = fields.Char(related='medium_classification_id.medium_classification_code',string='プロダクト中分類')
    minor_classification_code = fields.Char(related='minor_classification_id.minor_classification_code',string='プロダクト小分類')
    detail_classification_code = fields.Char(related='detail_classification_id.detail_classification_code',string='プロダクト詳細分類')


