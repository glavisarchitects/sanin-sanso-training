# -*- coding: utf-8 -*-
from odoo import models, fields, api


class IFDBPowerNetSalesHeadDetail(models.Model):
    _name = 'ss_erp.ifdb.powernet.sales.head.detail'
    _description = 'IFDB PowerNet Sales Head Detail'


    id = fields.Integer('ID', required=True, readonly=True)
    powernet_sales_header_id = fields.Many2one('ss_erp.ifdb.powernet.sales.header','PowerNet Sales Line Header')
    upload_date = fields.Datetime('Upload date and', required=True, index=True, readonly=True)
    name = fields.Char('Name')
    user_id = fields.Many2one('res.users', 'Manager', index=True)
    branch_id = fields.Many2one('ss_erp.organaization','Branch', index=True)
    status = fields.Selection(selection=[
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラー')
    ], string='Status', required=True, readonly=True)
    create_date = fields.Datetime('Created date',readonly=True)
    create_uid = fields.Many2one('res.users','Author', readonly=True)
    write_date = fields.Datetime('Last update', readonly=True)
    write_uid = fields.Many2one('res.users','Last updated',readonly=True)
    processing_date = fields.Datetime('Processing date and time', index=True, readonly=True)
    customer_code = fields.Char('Customer code', index=True,readonly=True)
    billing_summary_code = fields.Char('Billing summary code', readonly=True)
    sales_date = fields.Date('Sales date', index=True, readonly=True)
    slip_type = fields.Char('Slip type',readonly=True)
    slip_no = fields.Char('Slip No.',readonly=True)
    data_types = fields.Char('Data types', index=True,readonly=True)
    cash_classification = fields.Char('Cash / credit classification',readonly=True)
    product_code = fields.Char('Product code',readonly=True)
    product_code_2 = fields.Char('Product code 2',readonly=True)
    product_name = fields.Char('Product Name',readonly=True)
    product_remarks = fields.Char('Product Remarks',readonly=True)
    sales_category = fields.Char('Sales category',readonly=True)
    quantity = fields.Integer('Quantity',readonly=True)
    unit_code = fields.Char('Unit code', readonly=True)
    unit_price = fields.Float('Unit Price', readonly=True)
    amount_of_money = fields.Float('Amount of money', readonly=True)
    consumption_tax = fields.Float('Consumption tax', readonly=True)
    sales_amount = fields.Float('Sales Amount', readonly=True)
    quantity_after_conversion = fields.Float('Converted quantity',readonly=True)
    search_remarks_1 = fields.Char('Search Remark 1',readonly=True)
    search_remarks_2 = fields.Char('Search Remark 2', readonly=True)
    search_remarks_3 = fields.Char('Search Remark 3',readonly=True)
    search_remarks_4 = fields.Char('Search Remark 4',readonly=True)
    search_remarks_5 = fields.Char('Search Remark 5',readonly=True)
    search_remarks_6 = fields.Char('Search Remark 6',readonly=True)
    search_remarks_7 = fields.Char('Search Remark 7',readonly=True)
    search_remarks_8 = fields.Char('Search Remark 8',readonly=True)
    search_remarks_9 = fields.Char('Search Remark 9',readonly=True)
    search_remarks_10 = fields.Char('Search Remark 10',readonly=True)
    sales_classification_code_1 = fields.Char('Sales classification code 1',readonly=True)
    sales_classification_code_2 = fields.Char('Sales classification code 2',readonly=True)
    sales_classification_code_3 = fields.Char('Sales classification code 3',readonly=True)
    consumer_sales_classification_code_1 = fields.Char('Consumer Sales classification code 1',readonly=True)
    consumer_sales_classification_code_2 = fields.Char('Consumer Sales classification code 2',readonly=True)
    consumer_sales_classification_code_3 = fields.Char('Consumer Sales classification code 3',readonly=True)
    consumer_sales_classification_code_4 = fields.Char('Consumer Sales classification code 4',readonly=True)
    consumer_sales_classification_code_5 = fields.Char('Consumer Sales classification code 5',readonly=True)
    product_classification_code_1 = fields.Char('Product classification code 1',readonly=True)
    product_classification_code_2 = fields.Char('Product classification code 2',readonly=True)
    product_classification_code_3 = fields.Char('Product classification code 3',readonly=True)
    error_message = fields.Char('Error message',readonly=True)
    sale_id = fields.Many2one('sale.order','See sales order',readonly=True)

