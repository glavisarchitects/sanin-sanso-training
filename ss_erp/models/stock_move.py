from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_inventory_order_line_id = fields.Many2one('ss_erp.inventory.order.line')


