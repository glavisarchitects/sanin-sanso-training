from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_construction_order_id = fields.Many2one(related='picking_id.x_construction_order_id', store=True)
    x_workorder_id = fields.Many2one(related='picking_id.x_construction_order_id', store=True)
