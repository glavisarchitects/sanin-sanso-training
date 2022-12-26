from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_construction_order_id = fields.Many2one(related='picking_id.x_construction_order_id', store=True)
    x_construction_line_ids = fields.Many2many(
        'ss.erp.construction.component',
        'construction_order_line_stock_move_rel',
        'stock_move_id', 'construction_line_id',
        string='工事明細', readonly=True, copy=False)