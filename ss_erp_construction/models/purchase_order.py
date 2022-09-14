# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import html_translate
from odoo.tools.float_utils import float_round

import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_construction_order_id = fields.Many2one('ss.erp.construction', string='工事オーダー')

    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res.update({
            'x_construction_order_id': self.x_construction_order_id and self.x_construction_order_id.id or False,
        })
        return res