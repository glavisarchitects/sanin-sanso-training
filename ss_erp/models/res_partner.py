# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_fax_number = fields.Char(
        string="Fax Number", size=20
    )
    organization_id = fields.Many2one(
        'ss_erp.organization', string='Organization')
    x_contact_categ = fields.Many2one(
        'ss_erp.contact.category', string='Contact category', index=True,
        default=lambda self: self.env.ref(
            'ss_erp.ss_erp_contact_category_data_0', raise_if_not_found=False)
    )
    x_name_furigana = fields.Char(string="Furigana")
    x_partner_categ = fields.Selection([
        ('customer', 'Customer'),
        ('vendor', 'Supplier'),
        ('multi', 'Customers & Supplier'),
        ('other', 'Other'),
    ], string="Contact classification", help=_("Select Other for contacts not related to the transaction"))
    type = fields.Selection(selection_add=[
        ('for_rfq', 'Address for requesting a quote'),
        ('for_po', 'Order destination'),
    ])
    x_transaction_categ = fields.Many2many('ss_erp.bis.category', 'category_partner_rel',
                                           'categ_id', 'partner_id', string="Transaction classification", index=True)
    x_transaction_department = fields.Many2many(
        'ss_erp.bis.category', 'department_partner_rel', 'department_id', 'partner_id', string="Department", index=True)
    x_is_branch = fields.Boolean(string="Organization in charge", default=True, help=_(
        "Check if you have a place of responsibility, branch office, sales office, branch office"))

    x_branch_name = fields.Many2one(
        'ss_erp.organization', string='Name of organization in charge')
    x_fax = fields.Char('FAX representative')
    x_fax_payment = fields.Char('Fax payment notice')
    x_contract_check = fields.Selection([
        ('contract', '締結'),
        ('no_contract', '締結しない'),
        ('noting', '該当なし'),
    ], string='Transaction basic contract', default='contract', index=True)
    x_contract_memo = fields.Text(string="Reason for fluctuation")
    x_found_year = fields.Char(string='Founding year')
    x_capital = fields.Float(string='Capital')
    x_more_than_amount = fields.Float(string='Amount of 10,000 yen or more')
    x_more_than_deadline = fields.Float(
        string='Closing date of 10,000 yen or more')
    x_more_than_payment_site = fields.Char(
        string='Payment site for 10,000 yen or more')
    x_more_than_payment_method = fields.Selection([
        ('cash', '現金'),
        ('check', '小切手'),
        ('transfer', '振込'),
        ('bills', '手形'),
        ('offset', '相殺'),
    ], string='Payment method of 10,000 yen or more', default='transfer')
    x_less_than_amount = fields.Float(string='Amount of less than 10,000 yen')
    x_less_than_deadline = fields.Char(
        string='Closing date of 10,000 yen or less')
    x_less_than_payment_site = fields.Char(
        'Payment site for 10,000 yen or less')
    less_than_payment_method = fields.Selection([
        ('cash', '現金'),
        ('check', '小切手'),
        ('transfer', '振込'),
        ('bills', '手形'),
        ('offset', '相殺'),
    ], string='Payment method of 10,000 yen or less', default='transfer')
    x_collecting_money = fields.Selection([
        ('yes', '有'),
        ('no', '無'),
    ], string='Collecting money', default='no')
    x_fee_burden = fields.Selection([
        ('other_side', '先方'),
        ('our_side', '当方'),
    ], string='Fee burden', default='other_side')
    x_bill_site = fields.Char('Bill site', )
    x_purchase_user_id = fields.Many2one(
        'res.users', string='Purchasing person', index=True)
    x_vendor_payment_term = fields.Selection([
        ('ss_rule', '当社規定(規則参照)'),
        ('other', 'その他'),
    ], string='Payment terms and conditions')
    x_other_payment_term = fields.Char(string='Other payment terms')
    x_other_payment_reason = fields.Text(string='Reason for fluctuation')
    x_minimum_cost = fields.Float(string='Minimum purchase price')
    x_payment_terms = fields.Html(
        related='company_id.x_payment_terms', string='Our regulations on payment terms')
    x_customer_contract_route = fields.Text(string='Sales motive')
    x_customer_material = fields.Text(string='Products for sale')
    x_customer_monthly_total_price = fields.Float(
        string='Monthly sales amount')
    x_vendor_contract_route = fields.Text(string='Purchasing motive')
    x_vendor_material = fields.Text(string='Purchased products')
    x_vendor_monthly_total_price = fields.Float(
        string='Monthly purchase amount')
    performance_ids = fields.One2many(
        'ss_erp.partner.performance', 'partner_id', string='Partner performance')
    construction_ids = fields.One2many(
        'ss_erp.partner.construction', 'partner_id')
    # ADDITIONAL FIELD RELATED
    has_parent_id = fields.Selection(
        related='x_contact_categ.has_parent_id', store=True,)
    has_ref = fields.Selection(related='x_contact_categ.has_ref', store=True,)
    has_address = fields.Selection(
        related='x_contact_categ.has_address', store=True,)
    has_function = fields.Selection(
        related='x_contact_categ.has_function', store=True,)
    has_phone = fields.Selection(
        related='x_contact_categ.has_phone', store=True,)
    has_mobile = fields.Selection(
        related='x_contact_categ.has_mobile', store=True,)
    has_x_fax = fields.Selection(
        related='x_contact_categ.has_x_fax', store=True,)
    has_x_fax_payment = fields.Selection(
        related='x_contact_categ.has_x_fax_payment', store=True,)
    has_x_contract_check = fields.Selection(
        related='x_contact_categ.has_x_contract_check', store=True,)
    has_email = fields.Selection(
        related='x_contact_categ.has_email', store=True,)
    has_website = fields.Selection(
        related='x_contact_categ.has_website', store=True,)
    has_vat = fields.Selection(related='x_contact_categ.has_vat', store=True,)
    has_title = fields.Selection(
        related='x_contact_categ.has_title', store=True,)
    has_category_id = fields.Selection(
        related='x_contact_categ.has_category_id', store=True,)
    has_x_found_year = fields.Selection(
        related='x_contact_categ.has_x_found_year', store=True,)
    has_x_capital = fields.Selection(
        related='x_contact_categ.has_x_capital', store=True,)
    has_performance_info = fields.Selection(
        related='x_contact_categ.has_performance_info', store=True,)
    has_construction_info = fields.Selection(
        related='x_contact_categ.has_construction_info', store=True,)
    has_user_id = fields.Selection(
        related='x_contact_categ.has_user_id', store=True,)
    has_property_delivery_carrier_id = fields.Selection(
        related='x_contact_categ.has_property_delivery_carrier_id', store=True,)
    has_team_id = fields.Selection(
        related='x_contact_categ.has_team_id', store=True,)
    has_property_payment_term_id = fields.Selection(
        related='x_contact_categ.has_property_payment_term_id', store=True,)
    has_property_product_pricelist = fields.Selection(
        related='x_contact_categ.has_property_product_pricelist', store=True,)
    has_sales_term = fields.Selection(
        related='x_contact_categ.has_sales_term', store=True,)
    has_x_collecting_money = fields.Selection(
        related='x_contact_categ.has_x_collecting_money', store=True,)
    has_x_fee_burden = fields.Selection(
        related='x_contact_categ.has_x_fee_burden', store=True,)
    has_x_bill_site = fields.Selection(
        related='x_contact_categ.has_x_bill_site', store=True,)
    has_x_purchase_user_id = fields.Selection(
        related='x_contact_categ.has_x_purchase_user_id', store=True,)
    has_x_vendor_payment_term = fields.Selection(
        related='x_contact_categ.has_x_vendor_payment_term', store=True,)
    has_property_supplier_payment_term_id = fields.Selection(
        related='x_contact_categ.has_property_supplier_payment_term_id', store=True,)
    has_x_minimum_cost = fields.Selection(
        related='x_contact_categ.has_x_minimum_cost', store=True,)
    has_property_account_position_id = fields.Selection(
        related='x_contact_categ.has_property_account_position_id', store=True,)
    has_bank_accounts = fields.Selection(
        related='x_contact_categ.has_bank_accounts', store=True,)
    has_sales_note = fields.Selection(
        related='x_contact_categ.has_sales_note', store=True,)
    has_purchase_note = fields.Selection(
        related='x_contact_categ.has_purchase_note', store=True,)
    has_partner_info = fields.Boolean(related='x_contact_categ.has_partner_info', store=True)
    has_x_payment_terms = fields.Boolean(related='x_contact_categ.has_x_payment_terms', store=True)

    @api.depends('is_company', 'x_contact_categ')
    def _compute_company_type(self):
        for partner in self:
            if partner.x_contact_categ and partner.x_contact_categ.company_type:
                partner.company_type = partner.x_contact_categ.company_type
                print(33333333, partner.company_type)
            else:
                super(ResPartner, partner)._compute_company_type()

    @api.onchange
    def _onchange_x_contact_categ(self):
        if self.x_contact_categ and self.x_contact_categ.type:
            self.type = self.x_contact_categ.type
