# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import html_translate

import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_bis_categ_id = fields.Many2one('ss_erp.bis.category', string="Transaction classification", copy=True, index=True)
    x_po_type = fields.Selection([
        ('normal', 'Normal purchase'),
        ('industry_lorry', 'Raleigh delivery(industrial gas)'),
        ('lp_lorry', 'Raleigh delivery(LP gas)'),
        ('lng_lorry', 'Raleigh delivery(LNG gas)'),
        ('dropship', 'Direct delivery'),
    ], string="Purchase type", default='normal', index=True, copy=False)

    x_rfq_issue_date = fields.Date("Quotation request date")
    x_po_issue_date = fields.Date("Order sending date")
    x_desired_delivery = fields.Selection([
        ('full', 'Hope for full payment'),
        ('separated', 'Can be paid in installments'),
    ], string="Desired delivery", default='full', copy=True)
    x_dest_address_info = fields.Html("Direct shipping information")
    x_truck_number = fields.Char("Car number")
    x_organization_id = fields.Many2one('ss_erp.organization', string="Organization in charge", index=True)
    x_responsible_dept_id = fields.Many2one('ss_erp.responsible.department', string="Jurisdiction", index=True)
    x_mkt_user_id = fields.Many2one('res.users', string="Sales representative", index=True, default=lambda self: self.env.user)
    x_is_construction = fields.Boolean("Is construction?", compute='_compute_show_construction', compute_sudo=True)
    x_construction_name = fields.Char("Construction name")
    x_construction_sopt = fields.Char("construction site")
    x_construction_period_start = fields.Date("Scheduled construction period start")
    x_construction_period_end = fields.Date("Scheduled construction period ends")
    x_supplies_check = fields.Selection([
        ('no', 'No'),
        ('exist', 'Yes'),
    ], string="Presence or absence of supplies", default='no')
    x_supplies_info = fields.Char("Supplies")
    x_construction_payment_term = fields.Char("Payment terms", readonly=True, default=_("Construction payment conditions (deadline at the end of the month and payment at the end of the following month according to our regulations)"))

    x_explanation_check = fields.Selection([
        ('no', 'No'),
        ('exist', 'Yes'),
    ], string="Presence or absence of the current theory", default='no')
    x_explanation_date = fields.Date("Current date")
    x_explanation_spot = fields.Char("Current theory place")
    x_construction_other = fields.Text("others")
    x_construction_payment_cash = fields.Float("Cash")
    x_construction_payment_bill = fields.Float("Bills")
    x_construction_contract_notice = fields.Html("Notes on construction contract", copy=True, default=lambda self: self.env.user.company_id.x_construction_contract_notice)
    x_construction_subcontract = fields.Html("Estimated price and estimated period for subcontracting work", copy=True, default=lambda self: self.env.user.company_id.x_construction_subcontract)
    is_dropshipping = fields.Boolean('Is dropship', compute='_compute_is_dropshipping',)

    @api.depends('x_bis_categ_id')
    def _compute_show_construction(self):
        rec_construction_id = self.env.ref("ss_erp_master.ss_erp_bis_category_data_0", raise_if_not_found=False)
        for rec in self:
            rec.x_is_construction = True if rec_construction_id and self.x_bis_categ_id and self.x_bis_categ_id.id == rec_construction_id.id else False

    @api.depends('order_line', 'order_line.product_id')
    def _compute_is_dropshipping(self):
        for record in self:
            record.is_dropshipping = False
            if record.order_line:
                route_id = self.env.ref('stock_dropshipping.route_drop_shipping', raise_if_not_found=False)
                record.is_dropshipping = True if route_id in record.mapped('product_id').mapped('route_ids') else False

    @api.onchange('x_construction_payment_cash')
    def _onchange_construction_cash(self):
        if self.x_construction_payment_cash and self.clamp(self.x_construction_payment_cash):
            self.x_construction_payment_bill = 100 - self.x_construction_payment_cash

    @api.onchange('x_construction_payment_bill')
    def _onchange_construction_bills(self):
        if self.x_construction_payment_bill and self.clamp(self.x_construction_payment_bill):
            self.x_construction_payment_cash = 100 - self.x_construction_payment_bill

    @api.constrains("x_construction_payment_cash", "x_construction_payment_bill")
    def _check_sum_construction_payment(self):
        for record in self:
            cash = record.x_construction_payment_cash
            bills = record.x_construction_payment_bill
            if cash or bills:
                if sum([cash, bills]) != 100 or not(self.clamp(cash) or self.clamp(cash)):
                    raise ValidationError(_('Total payment must be 100%%: Cash %s%% - Bills %s%%' % (cash, bills)))

    def action_rfq_send(self):
        res = super(PurchaseOrder, self).action_rfq_send()
        if self.env.context.get('send_rfq', False):
            if self.x_is_construction:
                res['context'].update({
                    'default_template_id': self.env.ref("ss_erp_purchase.email_template_edi_purchase_construction").id
                })
            else:
                res['context'].update({
                    'default_template_id': self.env.ref("ss_erp_purchase.email_template_edi_purchase").id
                })
            res['context'].update({
                'partner_email_field': 'x_email_quote_request',
            })
        else:
            res['context'].update({
                'default_template_id': self.env.ref("ss_erp_purchase.email_template_edi_purchase_done").id
            })
            res['context'].update({
                'partner_email_field': 'x_email_purchase',
            })
        return res

    def print_quotation(self):
        res = super(PurchaseOrder, self).print_quotation()
        if self.x_is_construction:
            return self.env.ref('ss_erp_purchase.action_report_estimate_request').report_action(self)
        else:
            return self.env.ref('ss_erp_purchase.action_report_purchasequotation').report_action(self)
        return res

    @api.model
    def clamp(self, number):
        if number:
            if number < 0:
                return False
            elif number > 100:
                return False
            else:
                return number
