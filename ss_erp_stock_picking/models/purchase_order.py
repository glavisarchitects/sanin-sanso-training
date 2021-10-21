# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import html_translate

import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res.update({'user_id': self.user_id.id})
        return res
