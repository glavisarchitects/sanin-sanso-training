# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PartnerPerformance(models.Model):
    _name = 'ss_erp.partner.performance'
    _description = 'Partner performance'

    name = fields.Char(string='Name')
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)
    accounting_period = fields.Char(string='Fiscal year')
    revenue = fields.Float(string="Amount of sales")
    ordinary_profit = fields.Float(string="Management profit")
    partner_id = fields.Many2one('res.partner', string='Contact address')
