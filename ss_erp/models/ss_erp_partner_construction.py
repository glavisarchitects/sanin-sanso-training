# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PartnerConstruction(models.Model):
    _name = 'ss_erp.partner.construction'
    _description = 'Partner Construction'

    name = fields.Char(string='Name')
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)
    license_figure = fields.Char(string='Type of permission')
    license_flag_1 = fields.Selection([
        ('minister', '大臣'),
        ('governor', '知事'),
        ('other', 'その他')
    ], string='Minister / Governor classification', default='minister')
    license_flag_2 = fields.Selection([
        ('specific', '特定'),
        ('normal', '一般'),
        ('other', 'その他')
    ], string='Specific / general classification', default='normal')
    license_number = fields.Char(string='Permission number')
    license_period = fields.Date(string='Permit date')
    partner_id = fields.Many2one('res.partner', string='Contact address')
