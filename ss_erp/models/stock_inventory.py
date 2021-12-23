# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    organization_id = fields.Many2one('ss_erp.organization', string='Organization in charge')
    type_id = fields.Many2one('product.template', string='Inventory type')
    instruction_order_id = fields.Many2one('ss_erp.instruction.order', string='Inventory plan')
    state = fields.Selection(selection_add=[('approval', 'Approval')])
    name = fields.Char()
