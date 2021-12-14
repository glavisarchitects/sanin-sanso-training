# -*- coding: utf-8 -*-
from odoo import models, fields, api


class IFDBYGSummary(models.Model):
    _name = 'ss_erp.ifdb.yg.summary'
    _description = 'ヤマサンガスサプライ取込データ（検針集計表）'

    # name = fields.Char(string='Label dari Field')
    header_id = fields.Many2one(
        'ss_erp.ifdb.yg.header', string='ヤマサンガスサプライヘッダ')
    status = fields.Selection([
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり'),
    ], string='ステータス', default='wait', index=True)
    processing_date = fields.Datetime(
        string='処理日時', readonly=True)
    partner_id = fields.Char(string='販売店コード')
    # partner = fields.Char(string='Dealer code')
    amount_use = fields.Float(string='使用量')
    item = fields.Char(string='項目')
    sale_id = fields.Many2one('sale.order', string='販売オーダ参照')
    error_message = fields.Char(string='エラーメッセージ')
    detail_ids = fields.One2many(
        'ss_erp.ifdb.yg.detail', 'summary_id', string='YG detail')
