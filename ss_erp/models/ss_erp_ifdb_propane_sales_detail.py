from odoo import models, fields, api

class IFDBPropaneSalesDetail(models.Model):
    _name = 'ss_erp.ifdb.propane.sales.detail'
    _description = 'Propane sales file details'

    propane_sales_header_id = fields.Many2one('ss_erp.ifdb.propane.sales.header')
    status = fields.Selection([
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり'),
    ], string='Status', default='wait', index=True)
    processing_date = fields.Datetime(string='Processing date and time', readonly=True)
    external_data_type = fields.Char(string='External data type')
    customer_branch_code = fields.Char(string='Branch office C')
    customer_branch_sub_code = fields.Char(string='Branch office branch C')
    customer_business_partner_code = fields.Char(string='Advisor C')
    customer_business_partner_branch_code = fields.Char(string='Koeda C')
    customer_delivery_code = fields.Char(string='Contact information C')
    direct_branch_code = fields.Char(string='Direct branch C')
    direct_branch_sub_code = fields.Char(string='Direct branch branch C')
    direct_business_partner_code = fields.Char(string='Direct customer C')
    direct_business_partner_sub_code = fields.Char(string='Naoe C')
    direct_delivery_code = fields.Char(string='Direct delivery address C')
    customer_name = fields.Char(string='Customer name')
    commercial_branch_code = fields.Char(string='Commercial branch C')
    commercial_branch_sub_code = fields.Char(string='Commercial branch branch C')
    commercial_product_code = fields.Char(string='Commercial product C')
    product_name = fields.Char(string='Product name')
    standard_name = fields.Char(string='Standard name')
    standard = fields.Char(string='Standard')
    amount_of_money = fields.Float(string='Amount of money')
    unit_price_2 = fields.Float(string='Unit price 2')
    unified_quantity = fields.Float(string='Unified quantity')
    order_number = fields.Char(string='Order number')
    comment = fields.Char(string='Comment')
    commercial_branch_code2 = fields.Char(string='Commercial branch C2')
    commercial_branch_sub_code2 = fields.Char(string='Commercial branch branch C2')
    commercial_product_code2 = fields.Char(string='Commercial product C2')
    amount_calculation_classification = fields.Char(string='Amount calculation classification')
    slip_processing_classification = fields.Char(string='Slip processing classification')
    error_message = fields.Char(string='Error message')
    sale_id = fields.Many2one('sale.order',string='See sales order')
