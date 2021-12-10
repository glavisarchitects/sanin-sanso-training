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
    external_data_type = fields.Char(string='外部データ種別')

    customer_branch_code = fields.Char(string='顧支店Ｃ')
    customer_branch_sub_code = fields.Char(string='顧支店枝Ｃ')
    customer_business_partner_code = fields.Char(string='顧取引先Ｃ')
    customer_business_partner_branch_code = fields.Char(string='顧枝Ｃ')
    customer_delivery_code = fields.Char(string='顧届先Ｃ')
    direct_branch_code = fields.Char(string='直支店Ｃ')
    direct_branch_sub_code = fields.Char(string='直支店枝Ｃ')
    direct_business_partner_code = fields.Char(string='直取引先Ｃ')
    direct_business_partner_sub_code = fields.Char(string='直枝Ｃ')
    direct_delivery_code = fields.Char(string='直届先Ｃ')
    customer_name = fields.Char(string='取引先名')
    codeommercial_branch_code = fields.Char(string='商支店Ｃ')
    codeommercial_branch_sub_code = fields.Char(string='商支店枝Ｃ')
    codeommercial_product_code = fields.Char(string='商商品Ｃ')
    product_name = fields.Char(string='商品名')
    standard_name = fields.Char(string='規格名')
    standard = fields.Char(string='規格')

    # HuuPhong 091221
    number = fields.Char('本数')
    slip_number = fields.Char('伝票日')
    codelassification_code = fields.Char(string='分類Ｃ')
    line_break = fields.Char(string='行区分')
    quantity = fields.Char(string='数量')

    unit_code = fields.Char(string='単位Ｃ')
    unit_price = fields.Char(string='単価')
    amount_of_money = fields.Char(string='金額')
    unit_price_2 = fields.Char(string='単価２')
    amount_2 = fields.Char(string='金額２')
    unified_quantity = fields.Float(string='統一数量')
    order_number = fields.Char(string='注文番号')
    comment = fields.Char(string='コメント')
    codeommercial_branch_code2 = fields.Char(string='商支店Ｃ２')
    codeommercial_branch_sub_code2 = fields.Char(string='商支店枝Ｃ２')
    codeommercial_product_code2 = fields.Char(string='商商品Ｃ２')
    amount_calculation_classification = fields.Char(string='金額計算区分')
    slip_processing_classification = fields.Char(string='伝票処理区分')

    error_message = fields.Char(string='Error message')
    sale_id = fields.Many2one('sale.order',string='See sales order')


