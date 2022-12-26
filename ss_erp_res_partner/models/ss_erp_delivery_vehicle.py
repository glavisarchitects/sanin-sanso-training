# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DeliveryVehicle(models.Model):
    _name = 'ss_erp.delivery.vehicle'
    _description = '配送車両'

    name = fields.Char(string='配送車両')