# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import html_translate

import logging

_logger = logging.getLogger(__name__)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_fixed_cost = fields.Float("Purchase Fixed price")

    @api.onchange('product_id')
    def _onchange_product_id_sgvn(self):
        self.x_fixed_cost = self.product_id and self.product_id.x_fixed_cost
