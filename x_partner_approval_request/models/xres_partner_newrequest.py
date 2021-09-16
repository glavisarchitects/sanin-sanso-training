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
    _inherit = ["x.x_company_organization.org_mixin", "x.x_partner.partner_request_abstract"]
    _description = 'Partner New Request'

    # _inherits = {'res.partner': 'partner_id'}
    # _order = 'name'

    @api.model
    def default_transaction_classification(self):
        return self.env['x.transaction.classification'].search([('default', '=', True)]).ids

    @api.model
    def default_department_classification(self):
        return self.env['x.department.classification'].search([('default', '=', True)]).ids

    # partner_id = fields.Many2one('res.partner', required=True, ondelete='restrict', auto_join=True,
    #     string='Related Partner', help='Partner-related data of the user')

    user_id = fields.Many2one('res.users', '申請者', default=lambda self: self.env.user)
    state = fields.Selection([
        ('draft', 'ドラフト'),
        ('employee_send', '1次承認待ち'),
        ('branch_manager_approval', '2次承認待ち'),
        ('sale_head_approval', '3次承認待ち'),
        ('account_head_approval', '承認済み'),
    ], required=True, readonly=True, default='draft')
    name = fields.Char(default='新規', readonly=True)
    app_classification = fields.Selection([('new', '新規'), ('update', '更新'), ('branch_info', '支店の販売・購買情報追加')],
                                          default='new', string='申請区分')

    transaction_classification = fields.Many2many("x.transaction.classification",
                                                  default=default_transaction_classification,
                                                  string='取引区分')
    department_classification = fields.Many2many("x.department.classification",
                                                 default=default_department_classification, string='部門区分')

    apply_date = fields.Date(string='申請日')

    """ TODO:need to confirm branch """
    # apply_branch_id = fields.Many2one("res.branch",string='申請支店',)
    # employee_id = fields.Many2one(string='申請者')
    # employee_id = fields.Many2one(string='申請者', default=lambda self: self.env.user)

    """
        TODO reconfirm customer_code on res_partner
    """
    customer_id = fields.Many2one("res.partner", string='取引先', )
    customer_name = fields.Char(string='取引先名', default=lambda self: self.customer_id.name)
    street = fields.Char(string='町名番地')
    street2 = fields.Char(string='町名番地2')
    zip = fields.Char(string='郵便番号', change_default=True)
    city = fields.Char(string='市区町村')
    state_id = fields.Many2one("res.country.state", string='都道府県', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country',
                                 default=lambda self: self.env.ref("base.jp").id,  # @nhatnm0612
                                 string='Country', ondelete='restrict')

    partner_tel_representative = fields.Integer(string='取引先 TEL代表')
    partner_tel_direct = fields.Integer(string='取引先 TEL直通')

    request_organization_id = fields.Many2one(
        comodel_name='x.x_company_organization.res_org',
        string='申請組織',
        required=False)

    # change_design_230821
    # company_information = fields.Char('会社情報')
    company_id = fields.Many2one("res.company", string="会社", default=lambda self: self.env.user.company_id)

    # change_design_230821
    # our_payment_site = fields.Selection([('30_days_site', '30日サイト'), ('120_days_site', '120日サイト')], string='当社支払サイト')
    # reason_fluctuation  = fields.Text(string='支払条件変動理由')

    """"TODO: Recheck bank_name,branch_name,account_number on res.partner"""

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

    # organization_id = fields.Many2one( @nhatnm0612
    #     "x.x_company_organization.res_org", string="支店名称", default=lambda self: self.env.user.x_organization_id, @nhatnm0612
    #     help="Working organization of this user" @nhatnm0612
    # ) @nhatnm0612
    purchasing_person = fields.Char("購買担当者")
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

    # @api.onchange('transaction_classification')
    # def _onchange_transaction_classification(self):
    #     tran = self.transaction_classification
    #     if not tran:
    #         if len(tran) == 2 and tran in self.env["x.department.classification"].search([("name", "=", "ガス")]):
    #             self.department_classification = self.env['x.department.classification'].search(
    #                 [('name', '=', "ガス")]).ids
    #         if len(tran) == 2 and tran in self.env["x.department.classification"].search([("name", "=", "設備")]):
    #             self.department_classification = self.env['x.department.classification'].search(
    #                 [('name', '=', "器材")]).ids

    @api.onchange('customer_id')
    def _onchange_patner_id(self):
        self.x_partner_code = self.customer_id.x_partner_code
        self.customer_name = self.customer_id.name
        self.transaction_classification = [(6, 0, self.customer_id.x_transaction_classification.ids)]
        self.x_furigana_name = self.customer_id.x_furigana_name
        self.street = self.customer_id.street
        self.street2 = self.customer_id.street2
        self.state_id = self.customer_id.state_id
        self.city = self.customer_id.city
        self.zip = self.customer_id.zip
        self.partner_tel_representative = self.customer_id.phone
        self.partner_tel_direct = self.customer_id.mobile
        self.x_fax_number = self.customer_id.x_fax_number
        self.x_payment_notice_fax_number = self.customer_id.x_payment_notice_fax_number
        self.x_transaction_basic_contract = self.customer_id.x_transaction_basic_contract
        self.x_contract_not_apply_reason = self.customer_id.x_contract_not_apply_reason
        self.x_founding_year = self.customer_id.x_founding_year
        self.x_capital = self.customer_id.x_capital
        self.sale_information_ids = [(6, 0, self.customer_id.x_partner_performance.ids)]
        self.x_payment_term_using = self.customer_id.x_payment_term_using
        self.x_other_payment_term = self.customer_id.x_other_payment_term
        if self.customer_id.bank_ids:
            self.bank_name = self.customer_id.bank_ids[0].bank_name
            self.branch_name = self.customer_id.bank_ids[0].x_branch_name
            self.account_number = self.customer_id.bank_ids[0].acc_number
            self.deposit_item = self.customer_id.bank_ids[0].x_deposit_type
            self.account_holder = self.customer_id.bank_ids[0].acc_holder_name
            self.furigana_accname = self.customer_id.bank_ids[0].x_furigana

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
            # self.write({
            #     'state': 'account_head_approval'
            # })
            return {
                "type": "ir.actions.act_window",
                "name": _("Request Approval"),
                "target": "new",
                "res_model": "x.approval.checkbox",
                "view_mode": "form",
                "context": {
                    "default_x_partner_request_id": self.id,
                },
            }

    def write(self, vals):
        if vals.get('state') == 'account_head_approval':
            if self.app_classification == 'new':
                action_create_new_partner()
            else:
                action_update_partner()
        return super(PartnerRequest, self).write(vals)


    def action_create_new_partner(self):
        res_partner = self.env['res.partner']
        res_partner.create(
            {
                'x_partner_code': self.x_partner_code,
                'name': self.customer_name,
                'x_transaction_classification': [(6, 0, self.transaction_classification.ids)],
                'x_furigana_name': self.x_furigana_name,
                'street': self.street,
                'street2': self.street2,
                'state_id': self.state_id,
                'city': self.city,
                'zip': self.zip,
                'phone': self.partner_tel_representative,
                'mobile': self.partner_tel_direct,
                'x_fax_number': self.x_fax_number,
                'x_payment_notice_fax_number': self.x_payment_notice_fax_number,
                'x_transaction_basic_contract': self.x_transaction_basic_contract,
                'x_contract_not_apply_reason': self.x_contract_not_apply_reason,
                'x_founding_year': self.x_founding_year,
                'x_capital': self.x_capital,
                'x_partner_performance': [(6, 0, self.sale_information_ids.ids)],
                'x_payment_term_using': self.x_payment_term_using,
                'x_other_payment_term': self.x_other_payment_term,
                'bank_ids': [
                    (0, 0, {
                        'bank_name': self.bank_name,
                        'x_branch_name': self.branch_name,
                        'acc_number': self.account_number,
                        'x_deposit_type': self.deposit_item,
                        'acc_holder_name': self.account_holder,
                        'x_furigana': self.furigana_accname,
                    }),
                ],
            }
        )
        return res_partner

    def action_update_partner(self):
        res_partner = self.customer_id
        res_partner.update(
            {
                'x_partner_code': self.x_partner_code,
                'name': self.customer_name,
                'transaction_classification': [(6, 0, self.transaction_classification.ids)],
                'x_furigana_name': self.x_furigana_name,
                'street': self.street,
                'street2': self.street2,
                'state_id': self.state_id,
                'city': self.city,
                'zip': self.zip,
                'phone': self.partner_tel_representative,
                'mobile': self.partner_tel_direct,
                'x_fax_number': self.x_fax_number,
                'x_payment_notice_fax_number': self.x_payment_notice_fax_number,
                'x_transaction_basic_contract': self.x_transaction_basic_contract,
                'x_contract_not_apply_reason': self.x_contract_not_apply_reason,
                'x_founding_year': self.x_founding_year,
                'x_capital': self.x_capital,
                'x_partner_performance': [(6, 0, self.sale_information_ids.ids)],
                'x_payment_term_using': self.x_payment_term_using,
                'x_other_payment_term': self.x_other_payment_term,
                'bank_ids': [
                    (1, 0, {
                        'bank_name': self.bank_name,
                        'x_branch_name': self.branch_name,
                        'acc_number': self.account_number,
                        'x_deposit_type': self.deposit_item,
                        'acc_holder_name': self.account_holder,
                        'x_furigana': self.furigana_accname,
                    }),
                ],
            }
        )
        return res_partner

    def account_head_remand_partner_request(self):
        # self.write({
        #     'state': 'branch_manager_approval'
        # })
        if self.state == 'sale_head_approval':
            return {
                "type": "ir.actions.act_window",
                "name": _("Request Remand"),
                "target": "new",
                "res_model": "x.remand.checkbox",
                "view_mode": "form",
                "context": {
                    "default_x_partner_request_id": self.id,
                },
            }


class PartnerSalesInformation(models.Model):
    """
    model sale information
    """
    _inherit = "x.partner.sales.information"

    partner_request_id = fields.Many2one('x.res.partner.newrequest')


class PartnerAuthorizer(models.Model):
    """
    model Authorizer
    """
    _name = "x.partner.authorizer"
    _description = 'Partner Authorizer'

    partner_request_id = fields.Many2one('x.res.partner.newrequest')
    # authorizer = fields.Char("承認者")
    authorizer = fields.Many2one(
        comodel_name='res.users',
        string='承認者',
        required=False)
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
