# -*- coding: utf-8 -*-
from odoo import models, fields, api

CONTACT_CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'No'),
]


class ContactCategory(models.Model):
    _name = 'ss_erp.contact.category'
    _description = 'Contact Category'

    name = fields.Char(string='Name')
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)
    company_type = fields.Selection(
        [('person', 'Person'), ('company', 'Company')], string='Company type')
    type = fields.Selection([
        ('contact', 'Contacts'),
        ('invoice', 'Invoice'),
        ('delivery', 'Delivery to'),
        ('for_rfq', 'Address for requesting a quote'),
        ('for_po', 'Order destination'),
        ('other', 'Other addresses'),
        ('private', 'Personal address'),
    ], string='Address type')
    description = fields.Char(string='Explanation')
    basic = fields.Char('Basic')
    has_partner_info = fields.Boolean(
        string="Account Overview tab", default=True)
    has_parent_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='related company', default='required')
    has_ref = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Customer code', default='required')
    has_address = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Business address', default='required')
    has_function = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Job title', default='required')
    has_phone = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='TEL representative', default='required')
    has_mobile = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='TEL direct', default='required')
    has_x_fax = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='FAX representative', default='required')
    has_x_fax_payment = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Fax payment notice', default='required')
    has_x_contract_check = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Transaction basic contract', default='required')
    has_email = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Email', default='required')
    has_website = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Website link', default='required')
    has_vat = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Tax ID', default='required')
    has_title = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Title', default='required')
    has_category_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Tag', default='required')
    has_x_found_year = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Founding year', default='required')
    has_x_capital = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Capital', default='required')
    has_performance_info = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Achievement information', default='required')
    has_construction_info = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Construction permit', default='required')
    has_user_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Sales person', default='required')
    has_property_delivery_carrier_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Shipping method', default='required')
    has_team_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Sales team', default='required')
    has_property_payment_term_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Payment terms', default='required')
    has_property_product_pricelist = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Price list', default='required')
    has_sales_term = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Transaction terms', default='required')
    has_x_collecting_money = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Collecting money', default='required')
    has_x_fee_burden = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Fee burden', default='required')
    has_x_bill_site = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Bill site', default='required')
    has_x_purchase_user_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Purchasing person', default='required')
    has_x_vendor_payment_term = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Payment terms and conditions', default='required')
    has_property_supplier_payment_term_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Payment terms', default='required')
    has_x_minimum_cost = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Minimum purchase price', default='required')
    has_x_payment_terms = fields.Boolean(
        string='Our regulations on payment terms', default=True)
    has_property_account_position_id = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Accounting position', default='required')
    has_bank_accounts = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Bank accounts', default='required')
    has_sales_note = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Sales related', default='required')
    has_purchase_note = fields.Selection(
        CONTACT_CATEGORY_SELECTION, string='Purchasing related', default='required')

    @api.onchange('has_partner_info')
    def _onchange_has_partner_info(self):
        if not self.has_partner_info:
            self.has_x_found_year = 'no'
            self.has_x_capital = 'no'
            self.has_performance_info = 'no'
            self.has_construction_info = 'no'
