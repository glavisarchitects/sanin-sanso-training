# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    organization_id = fields.Many2one('ss_erp.organization', string='担当組織', states={'draft': [('readonly', False)]}, readonly=True)
    instruction_order_id = fields.Many2one('ss_erp.instruction.order', string='棚卸指示伝票')
    state = fields.Selection(string='Status', selection=[
        ('draft', 'ドラフト'),
        ('cancel', '取消済'),
        ('confirm', '進行中'),
        ('approval', '承認依頼中'),
        ('done', '承認完了')],
        copy=False, index=True, readonly=True, tracking=True,
        default='draft')

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