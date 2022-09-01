from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    inventory_order_line_id = fields.Many2one('ss_erp.inventory.order.line', string="移動オーダ明細")
    product_packaging = fields.Many2one(string='パッケージ', related='inventory_order_line_id.product_packaging', store=True)
    x_construction_order_id = fields.Many2one(related='picking_id.x_construction_order_id', store=True)
    x_workorder_id = fields.Many2one(related='picking_id.x_construction_order_id', store=True)
