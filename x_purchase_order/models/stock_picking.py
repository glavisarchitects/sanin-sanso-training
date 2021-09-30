# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _update_picking_from_group_key(self, key):
        for rec in self:
            for key_element in key:
                # if "date_planned" in key_element.keys():
                #     rec.date = key_element["date_planned"]
                if "location_dest_id" in key_element.keys() and key_element["location_dest_id"]:
                    rec.location_dest_id = key_element["location_dest_id"]

        return False
