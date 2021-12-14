# -*- coding: utf-8 -*-
from odoo import models, fields, api


class YoukiKensaBilling(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'ss_erp.ifdb.youkikensa.billing.file.header'
    _description = 'Youki Kensa Billing'

    name = fields.Char(string='名称')
    upload_date = fields.Datetime(
        string='アップロード日時', index=True, required=True,
		default=fields.Datetime.now())
    user_id = fields.Many2one('res.users', string='担当者', tracking=True)
    branch_id = fields.Many2one(
        'ss_erp.organization', string='支店', tracking=True)
    status = fields.Selection([
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり'),
    ], string='ステータス', default='wait', index=True)

    # processing_date = fields.Datetime('処理日時')
    # sales_date = fields.Datetime('処理日時')
    # slip_date = fields.Char('伝票No')
    # field_3 = fields.Char('フィールド3')
    # billing_code = fields.Char('請求先コード')
    # billing_abbreviation = fields.Char('請求先略称')
    # customer_code = fields.Char('得意先コード')
    # customer_abbreviation = fields.Char('得意先略称')
    # product_code = fields.Char('商品コード')
    # product_name = fields.Char('商品名')
    # unit_price = fields.Char('単価')
    # sales_return_quantity = fields.Char('販売返品数量')
    # net_sales_excluding_tax = fields.Char('税抜純売上高')
    # consumption_tax = fields.Char('消費税')
    # remarks = fields.Char('備考')
    # unit_cost = fields.Char('単位原価')
    # description = fields.Char('摘要')
    # error_message = fields.Char('エラーメッセージ')
    # purchase_id = fields.Many2one('purchase.order', '購買オーダ参照')

    youki_kensa_detail_ids = fields.One2many('ss_erp.ifdb.youkikensa.billing.file.detail', 'youkikensa_billing_file_header_id')


class YoukiKensaDetail(models.Model):
    _name = 'ss_erp.ifdb.youkikensa.billing.file.detail'
    _description = 'Youki Kensa Detail'

    youkikensa_billing_file_header_id = fields.Many2one('ss_erp.ifdb.youkikensa.billing.file.header')
    status = fields.Selection([
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり'),
    ], string='ステータス', default='wait', index=True)

    processing_date = fields.Datetime('処理日時')
    sales_date = fields.Datetime('処理日時')
    slip_no = fields.Char('伝票No')
    field_3 = fields.Char('フィールド3')
    billing_code = fields.Char('請求先コード')
    billing_abbreviation = fields.Char('請求先略称')
    customer_code = fields.Char('得意先コード')
    customer_abbreviation = fields.Char('得意先略称')
    product_code = fields.Char('商品コード')
    product_name = fields.Char('商品名')
    unit_price = fields.Char('単価')
    sales_return_quantity = fields.Char('販売返品数量')
    net_sales_excluding_tax = fields.Char('税抜純売上高')
    consumption_tax = fields.Char('消費税')
    remarks = fields.Char('備考')
    unit_cost = fields.Char('単位原価')
    description = fields.Char('摘要')
    error_message = fields.Char('エラーメッセージ')
    purchase_id = fields.Many2one('purchase.order', '購買オーダ参照')
