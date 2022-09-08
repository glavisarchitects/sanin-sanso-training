# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Organization(models.Model):
    _inherit = 'ss_erp.organization'

    warehouse_id = fields.Many2one('stock.warehouse', string="倉庫")