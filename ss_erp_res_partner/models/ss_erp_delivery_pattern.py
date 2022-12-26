# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DeliveryPattern(models.Model):
    _name = 'ss_erp.delivery.pattern'
    _description = '配信パターン'

    name = fields.Char(string='配信パターン')