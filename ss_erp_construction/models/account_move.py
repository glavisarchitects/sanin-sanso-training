# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_construction_order_id = fields.Many2one('ss.erp.construction', string='工事オーダー')