# -*- coding: utf-8 -*-
from odoo import models, fields, api


class IFDBPowerNetSalesHeadDetail(models.Model):
    _name = 'ss_erp.ifdb.powernet.sales.detail'
    _description = 'IFDB PowerNet Sales Detail'

    powernet_sales_header_id = fields.Many2one('ss_erp.ifdb.powernet.sales.header', 'PowerNetセールスヘッダー',
                                               required=True)
    status = fields.Selection(selection=[
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラー')
    ], string='ステータス', default="wait", required=True, readonly=True)
    processing_date = fields.Datetime('処理日時', index=True, readonly=True)
    customer_code = fields.Char('需要家コード', index=True, readonly=True)
    billing_summary_code = fields.Char('請求まとめコード', readonly=True)
    sales_date = fields.Date('売上日', index=True, readonly=True)
    slip_type = fields.Char('伝票種類', readonly=True)
    slip_no = fields.Char('伝票Ｎｏ', readonly=True)
    data_types = fields.Char('データ種類', index=True, readonly=True)
    cash_classification = fields.Char('現金／掛け区分', readonly=True)
    product_code = fields.Char('商品コード', readonly=True)
    product_code_2 = fields.Char('商品コード 2', readonly=True)
    product_name = fields.Char('商品名', readonly=True)
    product_remarks = fields.Char('商品備考', readonly=True)
    sales_category = fields.Char('売上区分', readonly=True)
    quantity = fields.Integer('数量', readonly=True)
    unit_code = fields.Char('単位コード', readonly=True)
    unit_price = fields.Float('単価', readonly=True)
    amount_of_money = fields.Float('金額', readonly=True)
    consumption_tax = fields.Float('消費税', readonly=True)
    sales_amount = fields.Float('売上額', readonly=True)
    quantity_after_conversion = fields.Float('換算後数量', readonly=True)
    search_remarks_1 = fields.Char('検索備考 1', readonly=True)
    search_remarks_2 = fields.Char('検索備考 2', readonly=True)
    search_remarks_3 = fields.Char('検索備考 3', readonly=True)
    search_remarks_4 = fields.Char('検索備考 4', readonly=True)
    search_remarks_5 = fields.Char('検索備考 5', readonly=True)
    search_remarks_6 = fields.Char('検索備考 6', readonly=True)
    search_remarks_7 = fields.Char('検索備考 7', readonly=True)
    search_remarks_8 = fields.Char('検索備考 8', readonly=True)
    search_remarks_9 = fields.Char('検索備考 9', readonly=True)
    search_remarks_10 = fields.Char('検索備考 10', readonly=True)
    sales_classification_code_1 = fields.Char('販売分類コード 1', readonly=True)
    sales_classification_code_2 = fields.Char('販売分類コード 2', readonly=True)
    sales_classification_code_3 = fields.Char('販売分類コード 3', readonly=True)
    consumer_sales_classification_code_1 = fields.Char('需要家販売分類コード 1', readonly=True)
    consumer_sales_classification_code_2 = fields.Char('需要家販売分類コード 2', readonly=True)
    consumer_sales_classification_code_3 = fields.Char('需要家販売分類コード 3', readonly=True)
    consumer_sales_classification_code_4 = fields.Char('需要家販売分類コード 4', readonly=True)
    consumer_sales_classification_code_5 = fields.Char('需要家販売分類コード 5', readonly=True)
    product_classification_code_1 = fields.Char('商品分類コード 1', readonly=True)
    product_classification_code_2 = fields.Char('商品分類コード 2', readonly=True)
    product_classification_code_3 = fields.Char('商品分類コード 3', readonly=True)
    error_message = fields.Char('エラーメッセージ', readonly=True)
    sale_id = fields.Many2one('sale.order', '販売オーダ参照', readonly=True)
    sale_ref = fields.Char(string="SOチェック用",
                           compute="_compute_sale_ref",
                           store=True)

    @api.depends("customer_code", "sales_date")
    def _compute_sale_ref(self):
        for r in self:
            sale_ref = ""
            if r.customer_code:
                sale_ref+="%s" % r.customer_code
            if r.sales_date:
                sale_ref+="%s" % r.sales_date
            r.sale_ref = sale_ref
