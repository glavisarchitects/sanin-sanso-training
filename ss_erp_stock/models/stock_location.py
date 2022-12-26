from odoo import fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    x_inventory_type = fields.Selection([('cylinder', 'シリンダー'), ('minibulk', 'ミニバルク'), ('others', 'その他')], string='棚卸タイプ')
    x_total_installation_quantity = fields.Float(string='総設置数量')

    x_stored_location = fields.Boolean(string='貯蔵品ロケーション', default=False)
