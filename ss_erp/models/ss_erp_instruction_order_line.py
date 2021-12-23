# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class InstructionOrderLine(models.Model):
    _name = 'ss_erp.instruction.order.line'
    _description = 'Instruction Slip Details'

    @api.model
    def _domain_location_id(self):
        return "[('usage', 'in', ['internal', 'transit'])]"

    categ_id = fields.Many2one('product.category', string='Product category')
    company_id = fields.Many2one('res.company', string='society')
    difference_qty = fields.Float(string='Difference')
    display_name = fields.Char(string='Display Name')
    inventory_date = fields.Datetime(string='Inventory adjustment date')
    inventory_id = fields.Many2one('stock.inventory', string='Stock')
    is_editable = fields.Boolean(string='Is it editable?')
    location_id = fields.Many2one('stock.location', string='Location', required=True,  domain=lambda self: self._domain_location_id())
    outdated = fields.Boolean(string='The quantity is out of date')
    package_id = fields.Many2one('stock.quant.package', string='Packing')
    partner_id = fields.Many2one('res.partner', string='Owner')
    prod_lot_id = fields.Many2one('stock.production.lot', string='Lot / Serial Number')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Many2one('stock.inventory.line', string='Inventory quantity')
    product_tracking = fields.Selection(string='Tracking', related='product_id.tracking')
    product_uom_id = fields.Many2one('uom.uom', string='Product unit', required=True)
    state = fields.Selection(string='Status', related='inventory_id.state')
    theoretical_qty = fields.Float()
    order_id = fields.Many2one('ss_erp.instruction.order', string='Order reference')
    organization_id = fields.Many2one('ss_erp.organization', related='order_id.organization_id',
                                      string='Organization name')
    type_id = fields.Many2one('product.template', related='order_id.type_id', string='Inventory type')
    stock_inventory_line_id = fields.Many2one('stock.inventory.line', string='Inventory details')
    product_cost = fields.Many2one('product.product', string='Unit price')

    @api.onchange('product_id')
    def _onchange_quantity_context(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
