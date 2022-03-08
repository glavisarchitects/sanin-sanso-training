# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    inventory_order_line_id = fields.Many2one(
        'ss_erp.instruction.order.line',
            string='棚卸指示明細番号')
    organization_id = fields.Many2one(
        'ss_erp.organization', string='組織名',
        related='inventory_order_line_id.organization_id')
    type_id = fields.Many2one(related='inventory_order_line_id.type_id', string='棚卸種別')
    product_cost = fields.Float(string='単価')

    def write(self, vals):
        res = super(StockInventoryLine, self).write(vals)
        for record in self:
            if record.inventory_order_line_id:
                record.inventory_order_line_id({
                    'product_cost': vals.get('product_cost', False),
                    'product_qty': vals.get('product_qty', False),
                })
        return res