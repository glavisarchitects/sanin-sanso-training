# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'


    x_product_unit_measure_ids = fields.One2many('ss_erp.product.units.measure',"product_id",string='代替単位')
