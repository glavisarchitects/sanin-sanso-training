from odoo import api, models, fields


class StockMove(models.Model):
    _inherit = "stock.move"

    x_lot_id = fields.Many2one('stock.production.lot', string='Lot No',
                               domain="[('company_id', '=', company_id), ('product_id', '=', product_id)]")
    x_quantity = fields.Float(string='Quantity', required=True, default=1)
    x_detail_no = fields.Char(string='Details No', readonly=True, required=True, copy=False, default='1')
    package_level_id = fields.Many2one('stock.package_level', 'Package Level', check_company=True, copy=False)
    x_package_qty = fields.Float(
        'Package Quantity',
        digits='Product Unit of Measure',
        default=0.0, required=True)
    x_package_unit = fields.Many2one('uom.uom', 'Package Unit', required=True, domain="[('category_id', '=', product_uom_category_id)]")


    # re-defines the field to change the default
    sequence = fields.Integer('HiddenSequence',
                              default=9999)

    # displays sequence on the stock moves
    sequence2 = fields.Integer('Sequence',
                               help="Shows the sequence in the Stock Move.",
                               related='sequence', readonly=True, store=True)

    @api.model
    def create(self, values):
        move = super(StockMove, self).create(values)
        # We do not reset the sequence if we are copying a complete picking
        # or creating a backorder
        if not self.env.context.get('keep_line_sequence', False):
            move.picking_id._reset_sequence()
        return move