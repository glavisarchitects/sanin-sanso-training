# -*- coding: utf-8 -*-
from odoo import models, fields, api

class IFDBYGHeader(models.Model):
    _name = 'ss_erp.ifdb.yg.header'
    _description = 'Yamasan Gas Supply Header'

    name = fields.Char(string='Name')
    upload_date = fields.Datetime(
        string='Upload date and time', index=True, required=True)
    user_id = fields.Many2one('res.users', string='Manager', tracking=True)
    branch_id = fields.Many2one(
        'ss_erp.organization', string='Branch', tracking=True)
    status = fields.Selection([
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり'),
    ], string='Status', default='wait', index=True)
    meter_reading_date = fields.Date(string='Meter reading date', index=True)
    summary_ids = fields.One2many(
        'ss_erp.ifdb.yg.summary', 'header_id', 'Meter reading summary table')
    detail_ids = fields.One2many(
        'ss_erp.ifdb.yg.detail', 'header_id', 'Meter reading detail table')

    def btn_processing_execution(self):
        return True