# -*- coding: utf-8 -*-
from odoo import models, fields, api


class IFDBPowerNetSalesHeadDetail(models.Model):
    _name = 'ss_erp.ifdb.powernet.sales.detail'
    _description = 'IFDB PowerNet Sales Detail'

    powernet_sales_header_id = fields.Many2one('ss_erp.ifdb.powernet.sales.header', 'PowerNet Sales Header',
                                               required=True)
    status = fields.Selection(selection=[
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラー')
    ], string='Status', default="wait", required=True, readonly=True)
    processing_date = fields.Datetime('Processing date and time', index=True)
    customer_code = fields.Char('Customer code', index=True)
    billing_summary_code = fields.Char('Billing summary code')
    sales_date = fields.Date('Sales date', index=True)
    slip_type = fields.Char('Slip type')
    slip_no = fields.Char('Slip No.')
    data_types = fields.Char('Data types', index=True)
    cash_classification = fields.Char('Cash / credit classification')
    product_code = fields.Char('Product code')
    product_code_2 = fields.Char('Product code 2')
    product_name = fields.Char('Product Name')
    product_remarks = fields.Char('Product Remarks')
    sales_category = fields.Char('Sales category')
    quantity = fields.Float('Quantity')
    unit_code = fields.Char('Unit code')
    unit_price = fields.Float('Unit Price')
    amount_of_money = fields.Float('Amount of money')
    consumption_tax = fields.Float('Consumption tax')
    sales_amount = fields.Float('Sales Amount')
    quantity_after_conversion = fields.Float('Converted quantity')
    search_remarks_1 = fields.Char('Search Remark 1')
    search_remarks_2 = fields.Char('Search Remark 2')
    search_remarks_3 = fields.Char('Search Remark 3')
    search_remarks_4 = fields.Char('Search Remark 4')
    search_remarks_5 = fields.Char('Search Remark 5')
    search_remarks_6 = fields.Char('Search Remark 6')
    search_remarks_7 = fields.Char('Search Remark 7')
    search_remarks_8 = fields.Char('Search Remark 8')
    search_remarks_9 = fields.Char('Search Remark 9')
    search_remarks_10 = fields.Char('Search Remark 10')
    sales_classification_code_1 = fields.Char('Sales classification code 1')
    sales_classification_code_2 = fields.Char('Sales classification code 2')
    sales_classification_code_3 = fields.Char('Sales classification code 3')
    consumer_sales_classification_code_1 = fields.Char('Consumer Sales classification code 1')
    consumer_sales_classification_code_2 = fields.Char('Consumer Sales classification code 2')
    consumer_sales_classification_code_3 = fields.Char('Consumer Sales classification code 3')
    consumer_sales_classification_code_4 = fields.Char('Consumer Sales classification code 4')
    consumer_sales_classification_code_5 = fields.Char('Consumer Sales classification code 5')
    product_classification_code_1 = fields.Char('Product classification code 1')
    product_classification_code_2 = fields.Char('Product classification code 2')
    product_classification_code_3 = fields.Char('Product classification code 3')
    error_message = fields.Char('Error message')
    sale_id = fields.Many2one('sale.order', 'Sales order')
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
