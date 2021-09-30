# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    date_issuance_order = fields.Date("Purchase order issuance date", copy=False)

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for order in self:
            order.write({'date_issuance_order': fields.Date.context_today(self)})
        return res

    def _check_unit_line_product(self, line):
        if not self.env.user.has_group('x_purchase_order.group_warning_unit_product_purchase'):
            return True
        if line.product_id.po_uom_ids and line.product_uom in line.product_id.po_uom_ids:
            return True
        return False

    def _check_qty_line_product(self, line):
        if not self.env.user.has_group('x_purchase_order.group_warning_qty_product_purchase'):
            return True
        line_qty = line.product_uom_qty
        if line.product_id.po_qty_confirm and line_qty <= line.product_id.po_qty_confirm:
            return True
        return False

    def _check_amount_line_product(self, line):
        if not self.env.user.has_group('x_purchase_order.group_warning_amount_product_purchase'):
            return True
        line_amount = line.price_subtotal
        if line.product_id.po_amount_confirm and line_amount <= line.product_id.po_amount_confirm:
            return True
        return False

    def action_button_confirm(self):
        msg = ""
        for order in self:
            for line in order.order_line:
                if not self._check_amount_line_product(line):
                    msg = _("The subtotal of the purchase order item exceeds the standard value.\n\nDo you want to place an order as it is?")
                    break
                if not self._check_qty_line_product(line):
                    msg = _("The quantity of the purchase order item exceeds the standard value.\n\nDo you want to place an order as it is?")
                    break
                if not self._check_unit_line_product(line):
                    msg = _("The unit of the purchase order item is a unit other than the set value.\n\nDo you want to place an order as it is?")
                    break
        if msg:
            action = {
                'name': _("Purchase order slip: Confirmed"),
                'type': 'ir.actions.act_window',
                'views': [[False, 'form']],
                'target': 'new',
                'context': {
                    'default_po_id': self.id,
                    'default_msg': msg,
                    'default_type': 'confirm',
                },
                'res_model': 'purchase.order.confirm.wizard'
            }
            return action
        return self.button_confirm()

    def action_button_cancel(self):
        msg = _("Do you want to cancel an order?")

        action = {
            'name': _("Purchase order slip: Cancel"),
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'target': 'new',
            'context': {
                'default_po_id': self.id,
                'default_msg': msg,
                'default_type': 'cancel',
            },
            'res_model': 'purchase.order.confirm.wizard'
        }
        return action

    def action_rfq_send(self):
        res = super(PurchaseOrder, self).action_rfq_send()
        if not self.env.context.get('send_rfq', False):
            res['context'].update({
                'default_template_id': self.env.ref("x_purchase_order.email_template_edi_purchase_done").id
            })
        res['context'].update({
            'partner_email_field': 'email_purchase',
        })
        return res

    # Unblock when Split picking with "date_planned"
    # def _check_split_pickings(self):
    #     for order in self:
    #         moves = self.env["stock.move"].search(
    #             [
    #                 ("purchase_line_id", "in", order.order_line.ids),
    #                 ("state", "not in", ("cancel", "done")),
    #             ]
    #         )
    #         pickings = moves.mapped("picking_id")
    #         pickings_by_date = {}
    #         for pick in pickings:
    #             pickings_by_date[pick.scheduled_date.date()] = pick
    #         order_lines = moves.mapped("purchase_line_id")
    #         date_groups = groupby(
    #             order_lines, lambda l: l._get_group_keys(l.order_id, l)
    #         )
    #         for key, lines in date_groups:
    #             date_key = fields.Date.from_string(key[0]["date_planned"])
    #             for line in lines:
    #                 for move in line.move_ids:
    #                     if move.state in ("cancel", "done"):
    #                         continue
    #                     if move.picking_id.scheduled_date.date() != date_key:
    #                         if date_key not in pickings_by_date:
    #                             copy_vals = line._first_picking_copy_vals(key, line)
    #                             new_picking = move.picking_id.copy(copy_vals)
    #                             pickings_by_date[date_key] = new_picking
    #                         move._do_unreserve()
    #                         move.picking_id = pickings_by_date[date_key]
    #                         move.date_deadline = date_key
    #         for picking in pickings_by_date.values():
    #             if len(picking.move_lines) == 0:
    #                 picking.write({"state": "cancel"})
