# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.models import NewId


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_default_country_id(self):
        return self.env['res.country'].search([('code', '=', 'JP'), ], limit=1)

    x_contact_categ = fields.Many2one(
        'ss_erp.contact.category', string='連絡先カテゴリ', index=True, tracking=True)

    x_transaction_categ = fields.Selection(
        [('gas_material', 'ガス・器材'),
         ('construction', '工事')],
        string='取引区分'
    )

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
    # x_transaction_categ = fields.Many2many('ss_erp.bis.category', 'category_partner_rel',
    #                                        'categ_id', 'partner_id', string="取引区分", index=True, tracking=True)
    # x_transaction_department = fields.Many2many(
    #     'ss_erp.bis.category', 'department_partner_rel', 'department_id', 'partner_id', string="部門", index=True,
    #     tracking=True)
    # x_is_branch = fields.Boolean(string="Organization in charge", default=True, help=_(
    #     "担当拠点、支店、営業所、出張所がある場合はチェック"), tracking=True)

    # x_branch_name = fields.Many2one(
    #     'ss_erp.organization', string='担当組織', tracking=True)
    x_fax = fields.Char('FAX代表', tracking=True)
    x_fax_payment = fields.Char('FAX支払通知書', tracking=True)
    x_contract_check = fields.Selection([
        ('contract', '締結'),
        ('no_contract', '締結しない'),
        ('noting', '該当なし'),
    ], string='取引基本契約書', index=True, default='contract', tracking=True,
        help='”新規取引、BtoB取引、継続的取引(スポットではない)、月間取引税込30万円以上” すべて該当する場合は必ず締結にする')
    x_contract_memo = fields.Text(string="変動理由", tracking=True)
    x_found_year = fields.Char(string='創立年度', tracking=True)
    x_capital = fields.Float(string='資本金', tracking=True)
    x_purchase_user_id = fields.Many2one(
        'res.users', string='購買担当者', index=True)
    x_other_payment_reason = fields.Text(string='変動理由', tracking=True)
    x_minimum_cost = fields.Monetary(string='最低仕入価格', tracking=True)
    x_payment_terms = fields.Html(
        related='company_id.x_payment_terms', string='支払条件の当社規定', tracking=True)

    x_contract_route = fields.Text(string='取引動機', tracking=True)
    x_material = fields.Text(string='販売/仕入商材', tracking=True)
    x_monthly_total_price = fields.Text(string='月間販売額/仕入額', tracking=True)

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
    # has_x_vendor_payment_term = fields.Selection(
    #     related='x_contact_categ.has_x_vendor_payment_term', store=True, )
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
    has_x_responsible_stamp = fields.Selection(
        related='x_contact_categ.has_x_responsible_stamp', store=True)

    has_industry_id= fields.Selection(
        related='x_contact_categ.has_industry_id', store=True)

    has_x_contract_route = fields.Selection(
        related='x_contact_categ.has_x_contract_route', store=True)
    has_x_contract_material = fields.Selection(
        related='x_contact_categ.has_x_contract_material', store=True)
    has_contract_monthly_amount = fields.Selection(
        related='x_contact_categ.has_contract_monthly_amount', store=True)

    has_lang = fields.Selection(related='x_contact_categ.has_lang', )

    x_payment_terms_ids = fields.One2many('ss_erp.partner.payment.term',
                                          'partner_id',
                                          string='Transaction terms')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=_get_default_country_id)
    # TuyenTN 2022/07/15
    # Lorry Business
    product_id = fields.Many2one('product.product', string='プロダクト')
    x_responsible_dept_id = fields.Many2one('ss_erp.responsible.department', string='管轄部門')
    # x_voucher_pattern
    x_lorry_type = fields.Selection([('industrial', '産ガス'),
                                     ('lpg', 'LPG'),
                                     ('lng', 'LNG')
                                     ], string='ローリー種別')
    x_name = fields.Many2many('ss_erp.delivery.vehicle', string='車両')
    x_acc_withdrawal = fields.Boolean(string='引落')
    x_acc_transfer = fields.Boolean(string='取引')
    x_received_method = fields.Many2one('account.journal', string='支払手段(入金)')
    x_responsible_person_printing = fields.Selection([('yes', '印字する'),
                                                      ('no', '印字しない'),
                                                      ], string="責任者の印字")
    # x_mini_bulk_business
    x_creation_target = fields.Boolean(string='配車計画一括作成')
    manager_id = fields.Many2one('hr.employee', string='担当者')
    x_delivery_pattern = fields.Many2one('ss_erp.delivery.pattern', string='配送パターン')
    x_delivery_reference_date = fields.Date(string='配送基準日')
    location_id = fields.Many2one('stock.location', string='在庫移動元(車両)')

    # TuyenTN 2022/29/07
    x_responsible_stamp = fields.Selection([('yes', '印字する'), ('no', '印字しない')], string='責任者の印字')
    x_more_than_deadline = fields.Char(string='締日(万円以上)')
    x_more_than_receipts_site = fields.Char(string='支払サイト(万円以上)')
    x_more_than_amount = fields.Float(string='金額(万円以上)')
    x_more_than_receipts_method = fields.Selection([('cash', '現金'), ('check', '小切手'),
                                                    ('bank', '振込'), ('transfer', '振替'), ('bills', '手形')],
                                                   string='入金手段(万円以上)', default='transfer')
    x_less_than_deadline = fields.Char(string='締日(万円以下)')
    x_less_than_receipts_site = fields.Char(string='支払サイト(万円以下)')
    x_less_than_amount = fields.Float(string='金額(万円以下)')
    less_than_receipts_method = fields.Selection([('cash', '現金'), ('check', '小切手'),
                                                  ('bank', '振込'), ('transfer', '振替'), ('bills', '手形')])
    x_collecting_money = fields.Selection([('yes', '印字する'), ('no', '印字しない')], default='no', string='集金')
    x_fee_burden = fields.Selection([('other_side', '先方'), ('out_side', '当方')], default='other_side', string='手数料負担')
    x_bill_site = fields.Char(string='手形サイト')
    x_payment_method = fields.Selection([('head_bank', '本社振込'), ('head_check', '本社手形'),
                                         ('bank_cash', '支店現金'), ('branch_bank', '支店振込')], string='支払手段')
    x_bank_payment_date = fields.Date(string='振込日')

    # has_x_payment_method = fields.Selection(
    #     related='x_contact_categ.has_x_payment_method',
    #     store=True)
    has_x_receipts_term = fields.Selection(
        related='x_contact_categ.has_x_receipts_term',
        store=True)
    # TuyenTN 08/18/2022 update F004
    x_payment_type = fields.Selection(string='支払手段', selection=[('bank', '振込'),
                                                                ('cash', '現金'),
                                                                ('heck', '本社手形')])
    has_x_payment_type = fields.Selection(related='x_contact_categ.has_x_payment_type', store=True)
    x_fee_burden_paid = fields.Selection([('other_side_paid', '先方負担'),
                                          ('our_side_paid', '当社負担')], string='支払手数料負担')
    has_x_fee_burden_paid = fields.Selection(related='x_contact_categ.has_x_fee_burden_paid', store=True)
    x_receipt_type_branch = fields.Selection([('bank', '振込'),
                                              ('transfer', '振替'),
                                              ('bills', '手形'),
                                              ('cash', '現金'),
                                              ('paycheck', '小切手'),
                                              ('branch_receipt', '他店入金'),
                                              ('offset', '相殺')
                                              ], string='入金手段')

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

    is_company = fields.Boolean(string='Is a Company', default=False,
        help="Check if the contact is a company, otherwise it is a person", compute='_compute_is_company', store=True)

    @api.depends('x_contact_categ')
    def _compute_is_company(self):
         for partner in self:
            if partner.x_contact_categ and partner.x_contact_categ.company_type == 'company':
                partner.is_company = True
            else:
                partner.is_company = False

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
            vals.pop('source')
            update_partner_form = False
        res = super(ResPartner, self).write(vals)
        if update_partner_form and len(vals) > 0 and self._name != 'ss_erp.res.partner.form':
            values = {}
            form_id = self.env['ss_erp.res.partner.form'].search([('res_partner_id', '=', self.id)])
            values.update({'source': 'res_partner'})
            for field_name, field_value in vals.items():
                if type(self._fields[field_name].compute) != str:
                    if self._fields[field_name].type in ['one2many', 'many2many']:
                        value = getattr(self, field_name, ())
                        value = [(6, 0, value.ids)] if value else False
                    else:
                        value = getattr(self, field_name)
                        if self._fields[field_name].type == 'many2one':
                            value = value.id if value else False
                values.update({field_name: value})
            form_id.write(values)
        return res

    def check_condition_show_dialog(self, vals=False, data_changed=False):
        corporation_id = self.env.ref('ss_erp.ss_erp_contact_category_data_1').id
        if vals.get('x_contact_categ') != corporation_id:
            return False

        if all([vals.get('zip'), vals.get('state_id'), vals.get('city'), vals.get('street'), vals.get('street2'),
                vals.get('x_contact_categ')]):
            # Check Duplicate Address
            dup_add = [('zip', '=', vals.get('zip')), ('state_id', '=', vals.get('state_id')),
                       ('city', '=', vals.get('city')), ('street', '=', vals.get('street')),
                       ('street2', '=', vals.get('street2')), ('x_contact_categ', '=', vals.get('x_contact_categ'))]
            if not isinstance(self.id, NewId):
                dup_add.append(('id', '!=', self.id))
            address_partner_fields = self.search(dup_add)
            if address_partner_fields:
                return True

        # Check Duplicate Name
        dup_name = [('name', '=', vals.get('name')), ('x_contact_categ', '=', vals.get('x_contact_categ'))]
        if not isinstance(self.id, NewId):
            dup_name.append(('id', '!=', self.id))
        dup_name_ids = self.search(dup_name)
        if dup_name_ids:
            return True

        # Check Duplicate Phone
        if vals.get('phone'):
            dup_phone = [('phone', '=', vals.get('phone')), ('x_contact_categ', '=', vals.get('x_contact_categ'))]
            if not isinstance(self.id, NewId):
                dup_phone.append(('id', '!=', self.id))
            dup_phone_ids = self.search(dup_phone)
            if dup_phone_ids:
                return True

        return False
