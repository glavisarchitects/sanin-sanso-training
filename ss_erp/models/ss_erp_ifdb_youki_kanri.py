# -*- coding: utf-8 -*-
from odoo import models, fields, api


class YoukiKanri(models.Model):
    _name = 'ss_erp.ifdb.youki.kanri'
    _description = 'Youki Kanri'

    name = fields.Char(string='名称')
    upload_date = fields.Datetime(
        string='アップロード日時', index=True, required=True)
    user_id = fields.Many2one('res.users', string='担当者', tracking=True)
    branch_id = fields.Many2one(
        'ss_erp.organization', string='支店', tracking=True)
    status = fields.Selection([
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり'),
    ], string='ステータス', default='wait', index=True)

    processing_date = fields.Datetime('処理日時')
    external_data_type = fields.Char('外部データ種別')
    customer_branch_code = fields.Char('顧支店Ｃ')
    customer_branch_sub_code = fields.Char('顧支店枝Ｃ')
    customer_business_partner_code = fields.Char('顧取引先Ｃ')
    customer_business_partner_branch_code = fields.Char('顧枝Ｃ')
    customer_delivery_code = fields.Char('顧届先Ｃ')
    direct_branch_code = fields.Char('直支店Ｃ')
    direct_branch_sub_code = fields.Char('直支店枝Ｃ')
    direct_business_partner_code = fields.Char('直取引先Ｃ')
    direct_business_partner_sub_code = fields.Char('直枝Ｃ')
    direct_delivery_code = fields.Char('直届先Ｃ')
    customer_name = fields.Char('取引先名')
    codeommercial_branch_code = fields.Char('商支店Ｃ')
    codeommercial_branch_sub_code = fields.Char('商支店枝Ｃ')
    codeommercial_product_code = fields.Char('商商品Ｃ')
    product_name = fields.Char('商品名')
    standard_name = fields.Char('規格名')
    standard = fields.Char('規格')
    number = fields.Char('本数')
    slip_date = fields.Date('伝票日')
    classification_code = fields.Char('分類Ｃ')
    line_break = fields.Char('行区分')
    quantity = fields.Char('数量')
    unit_code = fields.Char('単位Ｃ')
    unit_price = fields.Char('単価')
    amount_of_money = fields.Char('金額')
    unit_price_2 = fields.Char('単価２')
    amount_2 = fields.Char('金額２')
    unified_quantity = fields.Char('統一数量')
    order_number = fields.Char('注文番号')
    comment = fields.Char('コメント')
    codeommercial_branch_code2 = fields.Char('商支店Ｃ２')
    codeommercial_branch_sub_code2 = fields.Char('商支店枝Ｃ２')
    codeommercial_product_code2 = fields.Char('商商品Ｃ２')
    amount_calculation_classification = fields.Char('金額計算区分')
    slip_processing_classification = fields.Char('伝票処理区分')
    error_message = fields.Char('エラーメッセージ')
    sale_id = fields.Char('販売オーダ参照')
    purchase_id = fields.Char('購買オーダ参照')

    youki_kanri_detail_ids = fields.One2many('ss_erp.ifdb.youki.kanri.detail', 'ifdb_youki_kanri_id')


class YoukiKanriDetail(models.Model):
    _name = 'ss_erp.ifdb.youki.kanri.detail'
    _description = 'Youki Kanri Detail'

    name = fields.Char(string='名称')
    ifdb_youki_kanri_id = fields.Many2one('ss_erp.ifdb.youki.kanri', '容器管理IFDB')
    status = fields.Char('ステータス')
    processing_date = fields.Datetime('処理日時')
    external_data_type = fields.Char('外部データ種別')
    customer_branch_code = fields.Char('顧支店Ｃ')
    customer_branch_sub_code = fields.Char('顧支店枝Ｃ')
    customer_business_partner_code = fields.Char('顧枝Ｃ')
    customer_business_partner_branch_code = fields.Char('顧枝Ｃ')
    customer_delivery_code = fields.Char('顧届先Ｃ')
    direct_branch_code = fields.Char('直支店Ｃ')
    direct_branch_sub_code = fields.Char('直支店枝Ｃ')
    direct_business_partner_code = fields.Char('直取引先Ｃ')
    direct_business_partner_sub_code = fields.Char('直枝Ｃ')
    direct_delivery_code = fields.Char('直届先Ｃ')
    customer_name = fields.Char('取引先名')
    codeommercial_branch_code = fields.Char('商支店Ｃ')
    codeommercial_branch_sub_code = fields.Char('商支店枝Ｃ')
    codeommercial_product_code = fields.Char('商商品Ｃ')
    product_name = fields.Char('商品名')
    standard_name = fields.Char('規格名')
    standard = fields.Char('規格')
    number = fields.Char('本数')
    slip_date = fields.Char('伝票日')
    codelassification_code = fields.Char('分類Ｃ')
    line_break = fields.Char('行区分')
    quantity = fields.Char('数量')
    unit_code = fields.Char('単位Ｃ')
    unit_price = fields.Char('単価')
    amount_of_money = fields.Char('金額')
    unit_price_2 = fields.Char('単価２')
    amount_2 = fields.Char('金額２')
    unified_quantity = fields.Char('統一数量')
    order_number = fields.Char('注文番号')
    comment = fields.Char('コメント')
    codeommercial_branch_code2 = fields.Char('商支店Ｃ２')
    codeommercial_branch_sub_code2 = fields.Char('商支店枝Ｃ２')
    codeommercial_product_code2 = fields.Char('商商品Ｃ２')
    amount_calculation_classification = fields.Char('金額計算区分')
    slip_processing_classification = fields.Char('伝票処理区分')
    error_message = fields.Char('エラーメッセージ')
    sale_id = fields.Many2one('sale.order', '販売オーダ参照')
    purchase_id = fields.Many2one('purchase.order', '購買オーダ参照')
    inventory_order_id = fields.Many2one('ss_erp.inventory.order', '在庫移動伝票参照')