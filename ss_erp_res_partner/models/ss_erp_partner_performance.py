# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PartnerPerformance(models.Model):
    _name = 'ss_erp.partner.performance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '業績情報'

    name = fields.Char(string='名称')
    active = fields.Boolean('有効', default=True)
    sequence = fields.Integer('シーケンス')
    accounting_period = fields.Char(string='決算期')
    revenue = fields.Float(string="売上高")
    ordinary_profit = fields.Float(string="経営利益")
    partner_id = fields.Many2one('res.partner',string="連絡先")
    partner_form_id = fields.Many2one('ss_erp.res.partner.form',string="連絡先フォーム")
