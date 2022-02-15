# -*- coding: utf-8 -*-
from odoo import models, fields, api


class IFDBYGDetail(models.Model):
    _name = 'ss_erp.ifdb.yg.detail'
    _description = 'ヤマサンガスサプライ取込データ（検針明細表）'
    _order = 'customer_cd'

    summary_id = fields.Many2one('ss_erp.ifdb.yg.summary',string='ヤマサンガスサプライ検針集計表')
    header_id = fields.Many2one(
        'ss_erp.ifdb.yg.header', string='ヤマサンガスサプライヘッダ', related=False, store=True)
    item = fields.Char(string='項目')
    customer_cd = fields.Char(string='顧客コード')
    meter_reading_date = fields.Date(string='検針日')
    amount_use = fields.Float(string='使用量')
