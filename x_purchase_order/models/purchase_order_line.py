# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from itertools import groupby

import logging

_logger = logging.getLogger(__name__)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    fixed_price = fields.Float("Fixed price")

    @api.onchange('product_id')
    def _onchange_product_id_sgvn(self):
        self.fixed_price = self.product_id and self.product_id.po_fixed_price

    # Split picking with "location_dest_id" and "date_planned"
    @api.model
    def _get_group_keys(self, order, line, picking=False):
        # Split location value
        default_picking_location_id = line.order_id._get_destination_location()
        default_picking_location = self.env["stock.location"].browse(default_picking_location_id)
        location = line.location_dest_id or default_picking_location
        key = ({"location_dest_id": location},)

        # Unblock when Split picking with "date_planned"
        # date = line.date_planned.date()
        # key = ({"date_planned": fields.Date.to_string(date)},) + key
        return key

    @api.model
    def _first_picking_copy_vals(self, key, lines):
        vals = {"move_lines": []}
        for key_element in key:
            # Unblock when Split picking with "date_planned"
            # if "date_planned" in key_element.keys():
            #     vals["scheduled_date"] = key_element["date_planned"]
            if "location_dest_id" in key_element.keys():
                vals["location_dest_id"] = key_element["location_dest_id"].id
        return vals

    def _get_sorted_keys(self, line):
        keys = (line.location_dest_id.id,)
        # Unblock when Split picking with "date_planned"
        # keys = (line.date_planned,) + key
        return keys

    def _create_stock_moves(self, picking):
        """Group the receptions in one picking per group key"""
        moves = self.env["stock.move"]
        # Group the order lines by group key
        order_lines = sorted(
            self.filtered(lambda l: not l.display_type),
            key=lambda l: self._get_sorted_keys(l),
        )
        date_groups = groupby(
            order_lines, lambda l: self._get_group_keys(l.order_id, l, picking=picking)
        )

        first_picking = False
        # If a picking is provided, use it for the first group only
        if picking:
            first_picking = picking
            key, lines = next(date_groups)
            po_lines = self.env["purchase.order.line"]
            for line in list(lines):
                po_lines += line
            picking._update_picking_from_group_key(key)
            moves += super(PurchaseOrderLine, po_lines)._create_stock_moves(
                first_picking
            )

        for key, lines in date_groups:
            # If a picking is provided, clone it for each key for modularity
            if picking:
                copy_vals = self._first_picking_copy_vals(key, lines)
                picking = first_picking.copy(copy_vals)
            po_lines = self.env["purchase.order.line"]
            for line in list(lines):
                po_lines += line
            moves += super(PurchaseOrderLine, po_lines)._create_stock_moves(picking)

        for line in self:
            default_picking_location_id = line.order_id._get_destination_location()
            default_picking_location = self.env["stock.location"].browse(default_picking_location_id)
            location = line.location_dest_id or default_picking_location
            if location:
                line.move_ids.filtered(lambda m: m.state != "done").write(
                    {"location_dest_id": location.id}
                )
        return moves

    # Unblock when Split picking with "date_planned"
    # def write(self, values):
    #     res = super().write(values)
    #     if "date_planned" in values:
    #         self.mapped("order_id")._check_split_pickings()
    #     return res
