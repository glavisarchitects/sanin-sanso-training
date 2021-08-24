from odoo import api, models, fields


class StockMove(models.Model):
    _inherit = "stock.move"

    x_lot_id = fields.Many2one('stock.production.lot', string='Lot No',
                               domain="[('company_id', '=', company_id), ('product_id', '=', product_id)]")
    x_quantity = fields.Float(string='Quantity', required=True, default=1)
    x_detail_no = fields.Char(string='Details No', readonly=True, required=True, copy=False, default='01')
    package_level_id = fields.Many2one('stock.package_level', 'Package Level', check_company=True, copy=False)
    x_package_qty = fields.Float(
        'Package Quantity',
        digits='Product Unit of Measure',
        default=0.0, required=True, states={'done': [('readonly', True)]})
    x_package_unit = fields.Many2one('uom.uom', 'Package Unit', required=True, domain="[('category_id', '=', product_uom_category_id)]")

