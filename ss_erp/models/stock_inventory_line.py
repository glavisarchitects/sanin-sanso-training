# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    inventory_order_line_id = fields.Many2one(
        'ss_erp.instruction.order.line',
            string='Inventory instruction detail number')
    organization_id = fields.Many2one(
        'ss_erp.organization', string='Organization name',
        related='inventory_order_line_id.organization_id')
    type_id = fields.Many2one('product.template', string='Inventory type')
    product_cost = fields.Float(string='Unit price')
