# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_dropshipping = fields.Boolean(
        '直送であるか', compute='_compute_is_dropshipping',)

    @api.depends('order_line', 'order_line.product_id')
    def _compute_is_dropshipping(self):
        for record in self:
            record.is_dropshipping = False
            if record.order_line:
                route_id = self.env.ref(
                    'stock_dropshipping.route_drop_shipping', raise_if_not_found=False)
                record.is_dropshipping = True if route_id in record.mapped(
                    'product_id').mapped('route_ids') else False
