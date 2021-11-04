# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PartnerConstruction(models.Model):
    _name = 'ss_erp.partner.construction'
    _description = 'Partner Construction'

    name = fields.Char(string='Name')
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)
    license_figure = fields.Char(string='Type of permission')
    license_flag_1 = fields.Char(string='Minister / Governor classification')
    license_flag_2 = fields.Char(string='Specific / general classification')
    license_number = fields.Char(string='Permission number')
    license_period = fields.Date(string='Permit date')
    partner_id = fields.Many2one('res.partner', string='Contact address')