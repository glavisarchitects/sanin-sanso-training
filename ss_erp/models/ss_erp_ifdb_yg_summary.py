# -*- coding: utf-8 -*-
from odoo import models, fields, api

class IFDBYGSummary(models.Model):
    _name = 'ss_erp.ifdb.yg.summary'
    _description = 'Yamasan Gas Supply Meter Reading Summary Table'

    name = fields.Char(string='Label dari Field')
    header_id = fields.Many2one('ss_erp.ifdb.yg.header', string='Yamasan Gas Supply Header')
    status = fields.Selection([
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり'),
    ], string='Status', default='wait', index=True)
    processing_date = fields.Datetime(string='Processing date and time', readonly=True)
    partner_id = fields.Many2one('res.partner', string='')
    amount_use = fields.Float(string='Amount to use')
    item = fields.Char(string='Item')
    sale_id = fields.Many2one('sale.order', string='See sales order')
    error_message = fields.Char(string='Error message')
    detail_ids = fields.One2many(
        'ss_erp.ifdb.yg.detail', 'summary_id', string='YG detail')