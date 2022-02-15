# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PartnerConstruction(models.Model):
    _name = 'ss_erp.partner.construction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '建設業許可'

    name = fields.Char(string='名称')
    active = fields.Boolean('有効', default=True)
    sequence = fields.Integer('シーケンス', default=10)
    license_figure = fields.Char(string='許可の種類')
    license_flag_1 = fields.Selection([
        ('minister', '大臣'),
        ('governor', '知事'),
        ('other', 'その他')
    ], string='大臣･知事区分', default='minister')
    license_flag_2 = fields.Selection([
        ('specific', '特定'),
        ('normal', '一般'),
        ('other', 'その他')
    ], string='特定･一般区分', default='normal')
    license_number = fields.Char(string='許可番号')
    license_period = fields.Date(string='許可年月日')
    partner_id = fields.Many2one('res.partner', string='連絡先')
