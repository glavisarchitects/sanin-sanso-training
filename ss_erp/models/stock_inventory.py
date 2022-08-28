# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    organization_id = fields.Many2one('ss_erp.organization', string='担当組織', states={'draft': [('readonly', False)]}, readonly=True)
    instruction_order_id = fields.Many2one('ss_erp.instruction.order', string='棚卸指示伝票')
    state = fields.Selection(string='Status', selection=[
        ('draft', 'ドラフト'),
        ('confirm', '進行中'),
        ('approval', '承認依頼中'),
        ('done', '承認完了'),
        ('cancel', '取消済')],
        copy=False, index=True, readonly=True, tracking=True,
        default='draft')
    name = fields.Char()
    type_id = fields.Many2one('product.template', string='Inventory type', states={'draft': [('readonly', False)]},
                              readonly=True)

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

    def action_cancel_draft(self):
        res = super().action_cancel_draft()
        for inventory in self:
            if inventory.instruction_order_id:
                inventory.instruction_order_id.write({
                    'state': 'draft'
                })
        return res

    # change state to cancel
    def action_cancel(self):
        self.action_cancel_draft()
        self.write({
            'state': 'cancel'
        })
        # also cancel at approval
        approval_inventory_order_rec = self.env['approval.request'].search([('x_inventory_order_ids', 'in', self.id),
                                                             ('request_status', 'not in', ['cancel', 'refuse'])])
        if approval_inventory_order_rec:
            for approval in approval_inventory_order_rec:
                if len(approval.x_inventory_order_ids) > 1:
                    message = '棚卸伝票%sが棚卸操作で取消されたため、承認申請から削除されました。' % self.name
                    approval.sudo().write({'x_inventory_order_ids': [(3, self.id)]})
                    approval.message_post(body=message)
                else:
                    approval.sudo().update({
                        'request_status': 'cancel',
                    })
                    approval.message_post(body=_('承認申請の棚卸伝票が棚卸操作で取消されたため、承認申請を取消しました。'))