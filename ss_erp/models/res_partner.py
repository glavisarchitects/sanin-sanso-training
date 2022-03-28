# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_default_country_id(self):
        return self.env['res.country'].search([('code', '=', 'JP'), ], limit=1)

    x_contact_categ = fields.Many2one(
        'ss_erp.contact.category', string='連絡先カテゴリ', index=True, tracking=True)

    x_name_abbreviation = fields.Char(string='略称', tracking=True)
    x_name_furigana = fields.Char(string="フリガナ", tracking=True)

    ref = fields.Char(string='取引先コード', index=True)

    # 20211129
    x_is_customer = fields.Boolean(string='得意先', index=True, default=True, required=False, tracking=True)
    x_is_vendor = fields.Boolean(string='仕入先', index=True, default=True, required=False, tracking=True)
    type = fields.Selection(selection_add=[
        ('for_rfq', '見積依頼送付先'),
        ('for_po', '発注送付先'),
    ])
    x_transaction_categ = fields.Many2many('ss_erp.bis.category', 'category_partner_rel',
                                           'categ_id', 'partner_id', string="取引区分", index=True, tracking=True)
    x_transaction_department = fields.Many2many(
        'ss_erp.bis.category', 'department_partner_rel', 'department_id', 'partner_id', string="部門", index=True,
        tracking=True)
    x_is_branch = fields.Boolean(string="Organization in charge", default=True, help=_(
        "担当拠点、支店、営業所、出張所がある場合はチェック"), tracking=True)

    x_branch_name = fields.Many2one(
        'ss_erp.organization', string='担当組織', tracking=True)
    x_fax = fields.Char('FAX代表', tracking=True)
    x_fax_payment = fields.Char('FAX支払通知書', tracking=True)
    x_contract_check = fields.Selection([
        ('contract', '締結'),
        ('no_contract', '締結しない'),
        ('noting', '該当なし'),
    ], string='取引基本契約書', index=True, default='no_contract', tracking=True)
    x_contract_memo = fields.Text(string="変動理由", tracking=True)
    x_found_year = fields.Char(string='創立年度', tracking=True)
    x_capital = fields.Float(string='資本金', tracking=True)
    x_purchase_user_id = fields.Many2one(
        'res.users', string='購買担当者', index=True)
    x_vendor_payment_term = fields.Selection([
        ('ss_rule', '当社規定(規則参照)'),
        ('other', 'その他'),
    ], string='支払条件規定', tracking=True)
    x_other_payment_term = fields.Char(string='その他支払条件', tracking=True)
    x_other_payment_reason = fields.Text(string='変動理由', tracking=True)
    x_minimum_cost = fields.Float(string='最低仕入価格', tracking=True)
    x_payment_terms = fields.Html(
        related='company_id.x_payment_terms', string='支払条件の当社規定', tracking=True)
    x_customer_contract_route = fields.Text(string='販売動機', tracking=True)
    x_customer_material = fields.Text(string='販売商材', tracking=True)
    x_customer_monthly_total_price = fields.Float(
        string='月間販売額', tracking=True)
    x_vendor_contract_route = fields.Text(string='仕入動機', tracking=True)
    x_vendor_material = fields.Text(string='仕入商材', tracking=True)
    x_vendor_monthly_total_price = fields.Float(
        string='月間仕入額', tracking=True)
    performance_ids = fields.One2many(
        'ss_erp.partner.performance', 'partner_id', string='業績情報', tracking=True)
    construction_ids = fields.One2many(
        'ss_erp.partner.construction', 'partner_id', tracking=True)
    # ADDITIONAL FIELD RELATED
    has_parent_id = fields.Selection(
        related='x_contact_categ.has_parent_id', store=True, )
    has_ref = fields.Selection(related='x_contact_categ.has_ref', store=True, )
    has_address = fields.Selection(
        related='x_contact_categ.has_address', store=True, )
    has_function = fields.Selection(
        related='x_contact_categ.has_function', store=True, )
    has_phone = fields.Selection(
        related='x_contact_categ.has_phone', store=True, )
    has_mobile = fields.Selection(
        related='x_contact_categ.has_mobile', store=True, )
    has_x_fax = fields.Selection(
        related='x_contact_categ.has_x_fax', store=True, )
    has_x_fax_payment = fields.Selection(
        related='x_contact_categ.has_x_fax_payment', store=True, )
    has_x_contract_check = fields.Selection(
        related='x_contact_categ.has_x_contract_check', store=True, )
    has_email = fields.Selection(
        related='x_contact_categ.has_email', store=True, )
    has_website = fields.Selection(
        related='x_contact_categ.has_website', store=True, )
    has_vat = fields.Selection(related='x_contact_categ.has_vat', store=True, )
    has_title = fields.Selection(
        related='x_contact_categ.has_title', store=True, )
    has_category_id = fields.Selection(
        related='x_contact_categ.has_category_id', store=True, )
    has_x_found_year = fields.Selection(
        related='x_contact_categ.has_x_found_year', store=True, )
    has_x_capital = fields.Selection(
        related='x_contact_categ.has_x_capital', store=True, )
    has_performance_info = fields.Selection(
        related='x_contact_categ.has_performance_info', store=True, )
    has_construction_info = fields.Selection(
        related='x_contact_categ.has_construction_info', store=True, )
    has_user_id = fields.Selection(
        related='x_contact_categ.has_user_id', store=True, )
    has_property_delivery_carrier_id = fields.Selection(
        related='x_contact_categ.has_property_delivery_carrier_id', store=True, )
    has_team_id = fields.Selection(
        related='x_contact_categ.has_team_id', store=True, )
    has_property_payment_term_id = fields.Selection(
        related='x_contact_categ.has_property_payment_term_id', store=True, )
    has_property_product_pricelist = fields.Selection(
        related='x_contact_categ.has_property_product_pricelist', store=True, )
    has_sales_term = fields.Selection(
        related='x_contact_categ.has_sales_term', store=True, )
    has_x_collecting_money = fields.Selection(
        related='x_contact_categ.has_x_collecting_money', store=True, )
    has_x_fee_burden = fields.Selection(
        related='x_contact_categ.has_x_fee_burden', store=True, )
    has_x_bill_site = fields.Selection(
        related='x_contact_categ.has_x_bill_site', store=True, )
    has_x_purchase_user_id = fields.Selection(
        related='x_contact_categ.has_x_purchase_user_id', store=True, )
    has_x_vendor_payment_term = fields.Selection(
        related='x_contact_categ.has_x_vendor_payment_term', store=True, )
    has_property_supplier_payment_term_id = fields.Selection(
        related='x_contact_categ.has_property_supplier_payment_term_id', store=True, )
    has_x_minimum_cost = fields.Selection(
        related='x_contact_categ.has_x_minimum_cost', store=True, )
    has_property_account_position_id = fields.Selection(
        related='x_contact_categ.has_property_account_position_id', store=True, )
    has_bank_accounts = fields.Selection(
        related='x_contact_categ.has_bank_accounts', store=True, )
    has_sales_note = fields.Selection(
        related='x_contact_categ.has_sales_note', store=True, )
    has_purchase_note = fields.Selection(
        related='x_contact_categ.has_purchase_note', store=True, )
    has_partner_info = fields.Boolean(
        related='x_contact_categ.has_partner_info', store=True)
    has_x_payment_terms = fields.Boolean(
        related='x_contact_categ.has_x_payment_terms',
        store=True)
    x_payment_terms_ids = fields.One2many('ss_erp.partner.payment.term',
                                          'partner_id',
                                          string='Transaction terms')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=_get_default_country_id)

    @api.constrains('performance_ids', 'has_performance_info')
    def _check_performance_info_required(self):
        for record in self:
            if record.has_performance_info == 'required' and not record.performance_ids:
                raise ValidationError(_("業績情報は入力してください。"))

    @api.constrains('construction_ids', 'has_construction_info')
    def _check_construction_info_required(self):
        for record in self:
            if record.has_construction_info == 'required' and not record.construction_ids:
                raise ValidationError(_("建設業許可は入力してください。"))

    @api.constrains('bank_ids', 'has_bank_accounts')
    def _check_bank_accounts_required(self):
        for record in self:
            if record.has_bank_accounts == 'required' and not record.bank_ids:
                raise ValidationError(_("銀行口座は入力してください。"))

    @api.constrains('phone')
    def _check_default_phone(self):
        for record in self:
            if record.phone:
                partner = self.env['ss_erp.res.partner.form'].search([('phone', '=', self.phone)])
                if len(partner) > 1:
                    raise ValidationError(_("申請対象の取引先は、顧客または仕入先として既に登録済みの可能性があります。"))

    @api.constrains('x_transaction_categ')
    def _check_transaction_categ(self):
        for record in self:
            if record.x_is_customer or record.x_is_vendor:
                if len(record.x_transaction_categ) == 0:
                    raise ValidationError(_("取引区分は入力してください。"))

    @api.constrains('name')
    def _check_default_company_name(self):
        for record in self:
            if record.name:
                partner = self.search([('name', '=', self.name)])
                if len(partner) > 1:
                    raise ValidationError(_("申請対象の取引先は、顧客または仕入先として既に登録済みの可能性があります。"))

    @api.depends('is_company', 'x_contact_categ')
    def compute_company_type(self):
        for partner in self:
            if partner.x_contact_categ and partner.x_contact_categ.company_type:
                partner.company_type = partner.x_contact_categ.company_type
            else:
                super(ResPartner, partner).compute_company_type()

    @api.onchange("x_contact_categ")
    def _onchange_x_contact_categ(self):
        if self.x_contact_categ and self.x_contact_categ.type:
            self.type = self.x_contact_categ.type

    def write(self, vals):
        update_partner_form = True
        if vals.get('source'):
            vals.pop('source', None)
            update_partner_form = False
        res = super(ResPartner, self).write(vals)
        if update_partner_form:
            values = {}
            form_id = self.env['ss_erp.res.partner.form'].search([('res_partner_id', '=', self.id)], limit=1)
            values.update({'source': 'res_partner'})
            # form_id.write(vals)
            for name, field in self._fields.items():
                value = False
                if vals.get(name, None):
                    if self._fields[name].type in ['many2many', 'one2many']:
                        value = getattr(self, name, ())
                        value = [(6, 0, value.ids)] if value else False
                    elif self._fields[name].type == 'many2one':
                        value = getattr(self, name)
                        value = value.id if value else False
                    else:
                        value = vals[name]
                if value:
                    values.update({name: value})
            if len(values) > 1:
                form_id.write(values)
        return res
