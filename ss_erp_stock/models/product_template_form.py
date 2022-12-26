# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from lxml import etree
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class ProductTemplateForm(models.Model):
    _inherit = 'ss_erp.product.template.form'

    route_ids = fields.Many2many(
        'stock.location.route', 'ss_erp_stock_route_product_template_form', 'product_id', 'route_id', 'Routes',
        domain=[('product_selectable', '=', True)],
        help="Depending on the modules installed, this will allow you to define the route of the product: whether it will be bought, manufactured, replenished on order, etc.")

