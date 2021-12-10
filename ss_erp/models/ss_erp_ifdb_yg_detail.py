# -*- coding: utf-8 -*-
from odoo import models, fields, api


class IFDBYGDetail(models.Model):
    _name = 'ss_erp.ifdb.yg.detail'
    _description = 'Yamasan Gas Supply Meter Reading Summary Schedule'

    name = fields.Char(string='Name')
    summary_id = fields.Many2one('ss_erp.ifdb.yg.summary', required=True)
    item = fields.Char(string='Item')
    customer_cd = fields.Char(string='Customer code')
    meter_reading_date = fields.Date(string='Meter reading date')
    amount_use = fields.Float(string='Amount to use')
    processing_date = fields.Datetime(
        string='Processing date and time', readonly=True)
    header_id = fields.Many2one(
        'ss_erp.ifdb.yg.header', string='Yamasan Gas Supply Header', related='summary_id.header_id')
    error_message = fields.Char(string='Error message')
    sale_id = fields.Many2one('sale.order', string='See sales order')
    status = fields.Selection([
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり'),
    ], string='Status', default='wait', index=True)
