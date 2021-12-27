# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    x_partner_id = fields.Many2one(
        'res.users', string="Contact name", required=False,)
