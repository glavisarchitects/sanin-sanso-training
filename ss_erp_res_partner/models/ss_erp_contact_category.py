# -*- coding: utf-8 -*-
from odoo import models, fields, api

CONTACT_CATEGORY_SELECTION = [
    ('required', '必須'),
    ('optional', 'オプション'),
    ('no', 'なし'),
]


class ContactCategory(models.Model):
    _name = 'ss_erp.contact.category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '連絡先カテゴリ'

    name = fields.Char(string='名称')
    active = fields.Boolean('有効', default=True)
    sequence = fields.Integer('シーケンス', default=10)
    company_type = fields.Selection(
        [('person', '個人'), ('company', '会社')], string='会社タイプ')
    type = fields.Selection([
        ('contact', '連絡先'),
        ('invoice', '請求先'),
        ('delivery', '配送先'),
        ('for_rfq', '見積依頼送付先'),
        ('for_po', '発注送付先'),
        ('other', '他のアドレス'),
        ('private', '個人アドレス'),
    ], string='アドレスの種類')
    description = fields.Char(string='説明')
    has_partner_info = fields.Boolean(
        string="取引先概要タブ", default=True)
    has_parent_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='関連会社', default='optional')
    has_ref = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='取引先コード', default='optional')
    has_address = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='取引先住所', default='optional')
    has_function = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='職位', default='optional')
    has_phone = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='TEL代表', default='optional')
    has_mobile = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='TEL直通', default='optional')
    has_x_fax = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='FAX代表', default='optional')
    has_x_fax_payment = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='FAX支払通知書', default='optional')
    has_x_contract_check = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='取引基本契約書', default='optional')
    has_email = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Eメール', default='optional')
    has_website = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='ウェブサイトリンク', default='optional')
    has_vat = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='税ID', default='optional')
    has_title = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='タイトル', default='optional')
    has_category_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='タグ', default='optional')
    has_x_found_year = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='創立年度', default='optional')
    has_x_capital = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='資本金', default='optional')
    has_performance_info = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='実績情報', default='optional')
    has_construction_info = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='建設業許可', default='optional')

    has_user_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='販売担当者', default='optional')
    has_property_delivery_carrier_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='配送方法', default='optional')
    has_team_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='販売チーム', default='optional')
    has_property_payment_term_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='支払条件', default='optional')
    has_property_product_pricelist = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='価格リスト', default='optional')

    # 20220815
    has_partner_payment_term = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='支店別販売取引条件', default='optional')

    has_sales_term = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='取引条件', default='optional')
    has_x_collecting_money = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='集金', default='optional')
    has_x_fee_burden = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='手数料負担', default='optional')
    has_x_bill_site = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='手形サイト', default='optional')
    has_x_purchase_user_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='購買担当者', default='optional')
    has_property_supplier_payment_term_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='支払条件', default='optional')
    has_x_minimum_cost = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='最低仕入価格', default='optional')
    has_property_account_position_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='会計ポジション', default='optional')
    has_bank_accounts = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='銀行口座', default='optional')
    has_sales_note = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='販売関連', default='optional')
    has_purchase_note = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='仕入関連', default='optional')

    # HuuPhong 280722
    has_lang = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], string='言語')
    has_x_contract_route = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], string='取引動機')
    has_x_contract_material = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')],
                                               string='販売/仕入商材')
    has_contract_monthly_amount = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')],
                                                   string='月間販売/仕入額')
    has_x_responsible_stamp = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')],
                                               string='責任者の印字')
    has_x_receipts_term = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], string='取引条件')
    has_company_id = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], string='会社')
    has_industry_id = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], string='産業')

    has_x_payment_type = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], default='no',
                                          string='支払手段')
    has_x_fee_burden_paid = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], default='no',
                                             string='手数料負担')

    @api.onchange('has_partner_info')
    def _onchange_has_partner_info(self):
        if not self.has_partner_info:
            self.has_x_found_year = 'no'
            self.has_x_capital = 'no'
            self.has_performance_info = 'no'
            self.has_construction_info = 'no'
