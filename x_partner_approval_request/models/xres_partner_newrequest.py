# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

from werkzeug.urls import url_encode


class PartnerRequest(models.Model):
    """
    model request create new partner
    """
    _name = "x.res.partner.newrequest"
    _description = 'Partner New Request'
    # _inherits = {'res.partner': 'partner_id'}
    # _order = 'name'

    # partner_id = fields.Many2one('res.partner', required=True, ondelete='restrict', auto_join=True,
    #     string='Related Partner', help='Partner-related data of the user')
    state = fields.Selection([
        ('draft', 'ドラフト'),
        ('employee_send', '1次承認待ち'),
        ('branch_manager_approval', '2次承認待ち'),
        ('sale_head_approval', '3次承認待ち'),
        ('account_head_approval', '承認済み'),
    ], required=True, readonly=True, default='draft')
    name = fields.Char(default='新規', readonly=True)
    app_classification = fields.Selection([('new', '新規'), ('change', '変更')
                                           ], default='new', string='申請区分')
    partner_classification = fields.Selection([('customer', '得意先'), ('supplier', '仕入先')
                                               ], default='customer', string='取引先区分')
    transaction_classification = fields.Selection([('gas', 'ガス'), ('equipment', '器材')
                                                   ], default='gas', string='取引区分')
    department_classification = fields.Selection([('industry_gas', 'ガス'), ('medical_gas', '器材')
                                                  ], default='industry_gas', string='部門区分')

    apply_date = fields.Date(string='申請日')

    """ TODO:need to confirm branch """
    # apply_branch_id = fields.Many2one("res.branch",string='申請支店',)
    # employee_id = fields.Many2one(string='申請者')
    # employee_id = fields.Many2one(string='申請者', default=lambda self: self.env.user)

    customer_code = fields.Char(string='取引先コード', required=True)
    customer_name = fields.Char(string='取引先名')
    furigana_cusname = fields.Char(string='フリガナ', )
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')

    partner_tel_representative = fields.Integer(string='取引先 TEL代表')
    partner_tel_direct = fields.Integer(string='取引先 TEL直通')
    partner_fax_representative = fields.Integer(string='取引先 FAX代表')
    partner_fax_payment = fields.Integer(string='取引先 FAX支払通知書')
    transaction_basic_contract = fields.Selection(
        [('conclude', '締結'), ('not_conclude', '締結しない'), ('not_applicable', '該当なし')], string='理由記載')
    reason_description = fields.Text(string='理由記載')

    # change_design_230821
    company_information = fields.Char('会社情報')
    found_year = fields.Char(string='創立年度')
    capital = fields.Char(string='資本金')  # しほんきん

    # change_design_230821
    payment_terms = fields.Selection([('our_regulations', '当社規定'), ('other', 'その他')], string="支払条件")
    # our_payment_site = fields.Selection([('30_days_site', '30日サイト'), ('120_days_site', '120日サイト')], string='当社支払サイト')
    other_payment_terms = fields.Char(string='その他支払条件')
    reason_change_payment_terms = fields.Text(string='支払条件変動理由')
    # reason_fluctuation  = fields.Text(string='支払条件変動理由')

    bank_name = fields.Char(string='銀行名')
    branch_name = fields.Char(string='支店名')
    account_number = fields.Char(string='口座番号')
    deposit_item = fields.Selection([('normal', '普通'), ('current ', '当座')], string='預金種目')
    account_holder = fields.Char(string='口座名義')
    furigana_accname = fields.Char(string='フリガナ', )

    branch_information = fields.Char(string="支店情報")
    transaction_motive = fields.Char(string='取引動機')
    purchased_products = fields.Char(string='仕入商材')
    monthly_purchase_amount = fields.Char(string='月間仕入額')
    remarks = fields.Text("特記事項")
    contact_information = fields.Text("連絡事項")

    organization_id = fields.Many2one(
        "x.x_company_organization.res_org", string="支店名称", default=lambda self: self.env.user.x_organization_id,
        help="Working organization of this user"
    )
    purchasing_person = fields.Char("購買担当者")
    purchasing_area = fields.Char("購買地域")
    minimum_purchase_price = fields.Char("最低仕入価格")
    delivery_place = fields.Char("納品場所")

    # sale information ids
    sale_information_ids = fields.One2many('x.partner.sales.information', 'partner_request_id', string='業績情報')
    # Authorizer ids
    authorizer_ids = fields.One2many('x.partner.authorizer', 'partner_request_id', string='承認者')
    # x.partner.participants ids
    participants_ids = fields.One2many('x.partner.participants', 'partner_request_id', string='関係者')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('seq_x_partner_newrequest')
        return super(PartnerRequest, self).create(vals)

    def emp_confirm_partner_request(self):
        if self.state == 'draft':
            self.write({
                'state': 'employee_send'
            })

    def branch_manager_confirm_partner_request(self):
        if self.state == 'employee_send':
            self.write({
                'state': 'branch_manager_approval'
            })

    def branch_manager_remand_partner_request(self):
        self.write({
            'state': 'draft'
        })

    def sale_head_confirm_partner_request(self):
        if self.state == 'branch_manager_approval':
            self.write({
                'state': 'sale_head_approval'
            })

    def sale_head_remand_partner_request(self):
        self.write({
            'state': 'employee_send'
        })

    def account_head_confirm_partner_request(self):
        if self.state == 'sale_head_approval':
            self.write({
                'state': 'account_head_approval'
            })

    def account_head_remand_partner_request(self):
        self.write({
            'state': 'branch_manager_approval'
        })


class PartnerSalesInformation(models.Model):
    """
    model sale information
    """
    _name = "x.partner.sales.information"
    _description = 'Sale information'

    partner_request_id = fields.Many2one('x.res.partner.newrequest')
    fiscal_year = fields.Char(string='決算期')
    amount_of_sales = fields.Char(string='売上高')
    management_profit = fields.Char(string='経営利益')


class PartnerAuthorizer(models.Model):
    """
    model Authorizer
    """
    _name = "x.partner.authorizer"
    _description = 'Partner Authorizer'

    partner_request_id = fields.Many2one('x.res.partner.newrequest')
    authorizer = fields.Char("承認者")
    department = fields.Char(string='部署')
    update_date = fields.Date(string='更新日')
    """"TODO: re confirm status"""
    status = fields.Selection([('draft', 'ドラフト'), ('done', '仕入先登録済み'), ('cancle', '取消')], string='ステータス')


class PartnerParticipants(models.Model):
    """
    model participants
    """
    _name = "x.partner.participants"
    _description = 'Partner participants'

    partner_request_id = fields.Many2one('x.res.partner.newrequest')
    participant = fields.Char("承認者")
    department = fields.Char(string='部署')
    email = fields.Char(string='Eメールアドレス')

    def send_email(self):
        """"TODO: re confirm action send_email"""
        self.email
