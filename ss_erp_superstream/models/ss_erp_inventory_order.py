# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class InventoryOrder(models.Model):
    _inherit = 'ss_erp.inventory.order'

    is_super_stream_linked = fields.Boolean('SuperStream連携済', index=True, default=False, copy=False)
