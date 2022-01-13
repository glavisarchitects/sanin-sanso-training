# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    organization_id = fields.Many2one('ss_erp.organization', string='Organization in charge', states={'draft': [('readonly', False)]}, readonly=True)
    type_id = fields.Many2one('product.template', string='Inventory type', states={'draft': [('readonly', False)]}, readonly=True)
    instruction_order_id = fields.Many2one('ss_erp.instruction.order', string='Inventory plan')
    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'In Progress'),
        ('approval', 'Approval'),
        ('done', 'Validated')],
        copy=False, index=True, readonly=True, tracking=True,
        default='draft')
    state = fields.Selection(selection_add=[('approval', 'Approval')])
    name = fields.Char()

    def action_start(self):
        res = super().action_start()
        for inventory in self:
            if inventory.instruction_order_id:
                inventory.instruction_order_id.write({
                    'state': 'confirm'
                })
        return res

    def _action_done(self):
        negative = next((line for line in self.mapped('line_ids') if line.product_qty < 0 and line.product_qty != line.theoretical_qty), False)
        if negative:
            raise UserError(_(
                'You cannot set a negative product quantity in an inventory line:\n\t%s - qty: %s',
                negative.product_id.display_name,
                negative.product_qty
            ))
        self.action_check()
        self.write({'date': fields.Datetime.now()})
        self.post_inventory()
        return True