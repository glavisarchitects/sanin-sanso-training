# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'x.x_company_organization.org_mixin']

    @api.depends('trans_classify_id')
    def _compute_show_construction(self):
        for rec in self:
            rec.show_construction = True if self.trans_classify_id and self.trans_classify_id.code == 'construction' else False

    trans_classify_id = fields.Many2one('x.transaction.classification', "Transaction classification")
    type = fields.Selection([
        ('normal', 'Normal purchase'),
        ('tank_lorry', 'Truck delivery'),
    ], string='Purchase type', copy=False, default='normal')
    desired_delivery = fields.Selection([
        ('full', 'Full payment request'),
        ('separated', 'Can be paid in installments'),
    ], string="Desired delivery", copy=False, default='full')
    date_response = fields.Datetime("Response date", copy=False)
    date_issuance = fields.Date("Issuance date", copy=False, default=fields.Date.context_today)
    jurisdiction_id = fields.Many2one('crm.team', "Jurisdiction")
    dest_address_infor = fields.Html("Direct shipping information", copy=False)
    # Displayed only when the transaction classification item of the slip is "Construction"
    show_construction = fields.Boolean("Show Construction", compute='_compute_show_construction')
    construction_name = fields.Char("Construction name")
    construction_site = fields.Char("Construction site")
    construction_period_start = fields.Date('Scheduled construction period', copy=False)
    construction_period_end = fields.Date('Scheduled construction period (end)', copy=False)
    pres_abs_supplies = fields.Selection([
        ('none', 'Nothing'),
        ('having', 'Yes'),
    ], string="Presence/absence of supplies", copy=False, default='none')
    construction_supplies = fields.Char("Supplies")
    construction_payment_term = fields.Char("Payment terms", readonly=True, default=_("Dealine at the end of the month, payment at the end of the following month according to our regulations"))
    construction_cash = fields.Float("Cash")
    construction_bills = fields.Float("Bills")
    pres_abs_current_theory = fields.Selection([
        ('none', 'No'),
        ('explanation', 'Yes'),
    ], string='Presence/absence of the current theory', copy=False, default='none')
    construction_current_date = fields.Date('Date of the current theory', copy=False)
    construction_current_place = fields.Char('Current theory place', copy=False)
    construction_others = fields.Text('others', copy=False)
    notes_construction_contract = fields.Html("Notes on construction contract", related="company_id.notes_construction_contract")
    estimated_subcontracting_work = fields.Html("Estimated price and estimated period for subcontracting work", related="company_id.estimated_subcontracting_work")

    # Rename fields standard
    name = fields.Char(string="Slip No.")
    origin = fields.Char(string="Reference source")
    partner_id = fields.Many2one('res.partner', string="Supplier")
    user_id = fields.Many2one('res.users', string="Purchasing person")
    create_date = fields.Datetime(string="Create date")
    create_uid = fields.Many2one('res.users', string='Slip creator',)
    picking_type_id = fields.Many2one('stock.picking.type', string='Delivery destination',)
    dest_address_id = fields.Many2one('res.partner', string='Direct delivery',)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Accounting position',)
    date_planned = fields.Datetime(string="Requested delivery date")

    # TODO: Hide print with state
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(PurchaseOrder, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                         submenu=submenu)
        # _logger.info('111111111111111 fields_view_get toolbar print: %s', res.get('toolbar', {}).get('print', []))
        return res

    @api.onchange('partner_id')
    def _onchange_partner_id_sgvn(self):
        self.trans_classify_id = self.partner_id.x_transaction_classification and self.partner_id.x_transaction_classification[0].id
        x_organization_id = self.x_organization_id and self.x_organization_id.id
        if self.partner_id and not (self.partner_id.x_organization_id and self.partner_id.x_organization_id.id == x_organization_id):
            return {
                'warning': {
                    'title': _("Alert: Insufficient supplier transaction information"),
                    'message': _("""The purchasing information for [Login User's Organization Name] does not exist for the selected supplier.\nPlease complete the purchase information input / approval of the relevant supplier from the supplier application screen.""")
                },
            }

    @api.onchange('x_organization_id')
    def _onchange_x_organization_id(self):
        x_organization_id = self.x_organization_id and self.x_organization_id.id
        if self.partner_id and not (self.partner_id.x_organization_id and self.partner_id.x_organization_id.id == x_organization_id):
            return {
                'warning': {
                    'title': _("Alert: Insufficient supplier transaction information"),
                    'message': _("""The purchasing information for [Login User's Organization Name] does not exist for the selected supplier.\nPlease complete the purchase information input / approval of the relevant supplier from the supplier application screen.""")
                },
            }

    @api.onchange('construction_cash')
    def _onchange_construction_cash(self):
        if self.construction_cash and self.clamp(self.construction_cash):
            self.construction_bills = 100 - self.construction_cash

    @api.onchange('construction_bills')
    def _onchange_construction_bills(self):
        if self.construction_bills and self.clamp(self.construction_bills):
            self.construction_cash = 100 - self.construction_bills

    @api.constrains("construction_cash", "construction_bills")
    def _check_sum_construction_payment(self):
        for record in self:
            cash = record.construction_cash
            bills = record.construction_bills
            if cash or bills:
                if sum([cash, bills]) != 100 or not(self.clamp(cash) or self.clamp(cash)):
                    raise ValidationError(_('Total payment must be 100%%: Cash %s%% - Bills %s%%' % (cash, bills)))

    # Update file attachment for mail template with trans_classify_id in <![CDATA[]]>
    def action_rfq_send(self):
        res = super(PurchaseOrder, self).action_rfq_send()
        if self.env.context.get('send_rfq', False):
            if self.show_construction:
                res['context'].update({
                    'default_template_id': self.env.ref("x_purchase_quotation.email_template_edi_purchase_construction").id
                })
            else:
                res['context'].update({
                    'default_template_id': self.env.ref("x_purchase_quotation.email_template_edi_purchase").id
                })
        res['context'].update({
            'partner_email_field': 'email_quote_request',
        })
        return res

    def print_quotation(self):
        res = super(PurchaseOrder, self).print_quotation()
        if self.show_construction:
            return self.env.ref('x_purchase_quotation.action_report_estimate_request').report_action(self)
        else:
            return self.env.ref('x_purchase_quotation.action_report_purchasequotation').report_action(self)
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


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    location_dest_id = fields.Many2one('stock.location', "Delivery destination", domain=[("usage", "in", ["internal", "transit"])])
    # Rename fields standard
    product_uom_id = fields.Many2one('uom.uom', string='Unit',)
    taxes_id = fields.Many2many('account.tax', string='Tax',)

    @api.model
    def default_get(self, fields):
        rec = super(PurchaseOrderLine, self).default_get(fields)
        params = self._context.get('params')
        if params and params.get('id'):
            order_id = self.env['purchase.order'].browse(params.get('id'))
            rec['location_dest_id'] = order_id.x_organization_id.x_purchase_stock_location_id.id if order_id.x_organization_id and order_id.x_organization_id.x_purchase_stock_location_id else False
        else:
            x_organization_id = self.env.user.x_organization_id
            rec['location_dest_id'] = x_organization_id.x_purchase_stock_location_id.id if x_organization_id and x_organization_id.x_purchase_stock_location_id else False
        return rec

    # @api.onchange('order_id', 'order_id.x_organization_id')
    # def _onchange_partner_id_sgvn(self):
    #     self.location_dest_id = self.order_id.x_organization_id.x_purchase_stock_location_id.id if self.order_id.x_organization_id.x_purchase_stock_location_id else False
