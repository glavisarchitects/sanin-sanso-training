# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    organization_id = fields.Many2one('ss_erp.organization', string='Organization in charge', states={'draft': [('readonly', False)]}, readonly=True)
    type_id = fields.Many2one('product.template', string='Inventory type', states={'draft': [('readonly', False)]}, readonly=True)
    instruction_order_id = fields.Many2one('ss_erp.instruction.order', string='Inventory plan')
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
