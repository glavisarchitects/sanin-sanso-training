# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_construction_order_id = fields.Many2one('ss.erp.construction', string='工事オーダー')
    x_workorder_id = fields.Many2one('ss.erp.construction.workorder', string='作業オーダー')
