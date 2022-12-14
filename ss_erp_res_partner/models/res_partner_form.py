# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from lxml import etree

_logger = logging.getLogger(__name__)


class ResPartnerForm(models.Model):
    _name = 'ss_erp.res.partner.form'
    _inherit = 'res.partner'
    _description = 'Res Partner Form'

    approval_id = fields.Char(string="Approval ID")
    approval_state = fields.Char(string='Approval status')
    res_partner_id = fields.Char(string='Contact ID')

    # Override fields and fucntion in res.partner
    channel_ids = fields.Many2many(
        'mail.channel', 'ss_erp_mail_channel_profile_partner_form', 'partner_id', 'channel_id', copy=False)
    meeting_ids = fields.Many2many('calendar.event', 'ss_erp_calendar_event_res_partner_form_rel',
                                   'res_partner_id', 'calendar_event_id', string='Meetings', copy=False)

    property_account_payable_id = fields.Many2one('account.account', string="Account Payable",
                                                  domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
                                                  help="This account will be used instead of the default one as the payable account for the current partner",
                                                  default=lambda self: self._default_property_account_payable_id(),
                                                  required=False)
    property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
                                                     string="Account Receivable",
                                                     domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
                                                     help="This account will be used instead of the default one as the receivable account for the current partner",
                                                     default=lambda
                                                         self: self._default_property_account_receivable_id(),
                                                     required=False)
    same_vat_partner_id = fields.Many2one(
        'res.partner', string='Partner with same Tax ID', store=False)

    property_stock_customer = fields.Many2one(
        'stock.location', string="Customer Location", company_dependent=True, check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', allowed_company_ids[0])]",
        help="The stock location used as destination when sending goods to this contact.",
        default=lambda self: self.env.ref('stock.stock_location_customers', raise_if_not_found=False))
    property_stock_supplier = fields.Many2one(
        'stock.location', string="Vendor Location", company_dependent=True, check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', allowed_company_ids[0])]",
        help="The stock location used as source when receiving goods from this contact.",
        default=lambda self: self.env.ref('stock.stock_location_suppliers', raise_if_not_found=False))
    user_id = fields.Many2one(
        comodel_name='res.users', default=lambda self: self.env.uid)

    @api.model
    def _default_property_account_payable_id(self):
        return self.env['ir.property']._get('property_account_payable_id', 'res.partner')

    @api.model
    def _default_property_account_receivable_id(self):
        return self.env['ir.property']._get('property_account_receivable_id', 'res.partner')

    # Override one2many field -> many2many field
    activity_ids = fields.Many2many(
        'mail.activity', 'ss_erp_mail_activity_res_partner_form_rel', 'partner_id', 'activity_id', string="Activities",
        copy=False)
    bank_ids = fields.Many2many(
        'res.partner.bank', 'ss_erp_res_partner_bank_res_partner_form_rel', 'partner_id', 'bank_id', string="Banks",
        copy=False)

    # 20220822
    x_payment_terms_ids = fields.Many2many(
        'ss_erp.partner.payment.term', 'ss_erp_partner_payment_term_res_partner_form_rel', 'partner_id', 'payment_terms_id', string="Contact", copy=False)

    child_ids = fields.Many2many(
        'ss_erp.res.partner.form', 'ss_erp_res_partner_form_child_res_partner_form_rel', 'partner_form_id', 'child_id', string="Contact", copy=False)

    construction_ids = fields.Many2many('ss_erp.partner.construction', 'ss_erp_partner_construction_res_partner_form_rel',
                                        'partner_id', 'construction_id', string="Construction", copy=False)
    contract_ids = fields.Many2many(
        'account.analytic.account', 'ss_erp_analytic_account_res_partner_form_rel', 'partner_id', 'account_id', copy=False)
    invoice_ids = fields.Many2many(
        'account.move', 'account_move_res_partner_form_rel', 'partner_id', 'account_move_id', copy=False)
    message_follower_ids = fields.Many2many(
        'mail.followers', 'ss_erp_mail_followers_res_partner_form_rel', 'partner_id', 'followers_id', copy=False)
    message_ids = fields.Many2many(
        'mail.message', 'ss_erp_mail_message_res_partner_form_rel', 'partner_id', 'message_id', copy=False)
    payment_token_ids = fields.Many2many(
        'payment.token', 'ss_erp_payment_token_res_partner_form_rel', 'partner_id', 'token_id', copy=False)
    performance_ids = fields.Many2many(
        'ss_erp.partner.performance', 'ss_erp_partner_performance_res_partner_form_rel', 'partner_id',
        'partner_performance_id', copy=False)
    purchase_line_ids = fields.Many2many(
        'purchase.order.line', 'ss_erp_po_line_res_partner_form_rel', 'partner_id', 'po_line_id', copy=False)
    ref_company_ids = fields.Many2many(
        'res.company', 'ss_erp_res_company_res_partner_form_rel', 'partner_id', 'res_company_id', copy=False)
    sale_order_ids = fields.Many2many(
        'sale.order', 'ss_erp_sale_order_res_partner_form_rel', 'partner_id', 'sale_order_id', copy=False)
    user_ids = fields.Many2many(
        'res.users', 'ss_erp_res_users_res_partner_form_rel', 'partner_id', 'res_users_id', copy=False)
    website_message_ids = fields.Many2many(
        'mail.message', 'ss_erp_web_mail_message_res_partner_form_rel', 'partner_id', 'mail_message_id', copy=False)

    parent_id = fields.Many2one(
        "ss_erp.res.partner.form", string='?????????')

    @api.model
    def _commercial_fields(self):
        return super(ResPartnerForm, self)._commercial_fields() + \
               ['debit_limit', 'property_account_payable_id', 'property_account_receivable_id',
                'property_account_position_id',
                'property_payment_term_id', 'property_supplier_payment_term_id', 'last_time_entries_checked']

    # Override to fix conflict
    @api.depends('is_company', 'parent_id.commercial_partner_id')
    def _compute_commercial_partner(self):
        for partner in self:
            partner.commercial_partner_id = False

    @api.depends('user_ids.share', 'user_ids.active')
    def _compute_partner_share(self):
        for partner in self:
            partner.partner_share = False

    @api.depends('purchase_line_ids')
    def _compute_on_time_rate(self):
        for partner in self:
            partner.on_time_rate = -1

    def _message_add_suggested_recipient(self, result, partner=None, email=None, reason=''):
        return result

    def name_get(self):
        results = []
        for rec in self:
            results.append((rec.id, rec.name))
        return results

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('ref', 'ilike', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    # New
    def write(self, values):
        update_res_partner = True
        if values.get('source', False) and values.get('source') == 'res_partner':
            values.pop('source', None)
            update_res_partner = False
        if self._name == 'ss_erp.res.partner.form':
            res = super(ResPartnerForm, self).write(values)
            if 'approval_state' in values and values.get('approval_state') == 'approved' and update_res_partner:
                self._action_process()
                if self.parent_id:
                    self.parent_id._action_process()
                self.child_ids._action_process()
                self._update_parent_for_child()
            return res
        else:
            return True

    def _update_parent_for_child(self):
        # Update parernt
        if self.parent_id:
            parent_id = int(self.parent_id.res_partner_id)
            partner_id = self.env['res.partner'].browse(int(self.res_partner_id))
            partner_id.write({'parent_id':parent_id})

        # Update child
        new_parent_id = int(self.res_partner_id)
        for rec in self.child_ids:
            partner_id = self.env['res.partner'].browse(int(rec.res_partner_id))
            partner_id.write({'parent_id': new_parent_id})


    def _action_process(self):
        DEFAULT_FIELDS = ['id', 'create_uid', 'create_date', 'write_uid', 'write_date',
                          '__last_update', 'approval_id', 'approval_state', 'meeting_ids']

        MANY2MANY_FIELDS = ['construction_ids','contract_ids','invoice_ids','purchase_line_ids','sale_order_ids', 'child_ids','parent_id']

        for form_id in self:
            vals = {}

            for name, field in form_id._fields.items():
                if name in MANY2MANY_FIELDS:
                    continue
                else:
                    if name not in DEFAULT_FIELDS and \
                            form_id._fields[name].type not in ['one2many'] and \
                            type(form_id._fields[name].compute) != str:
                        if form_id._fields[name].type == 'many2many':
                            value = getattr(form_id, name, ())
                            value = [(6, 0, value.ids)] if value else False
                        else:
                            value = getattr(form_id, name)
                            if form_id._fields[name].type == 'many2one':
                                value = value.id if value else False

                        vals.update({name: value})
            res_partner_id = vals.pop('res_partner_id')
            if not res_partner_id:
                # Create partner with contact form
                partner_id = self.env['res.partner'].sudo().create(vals)
                form_id.write({'res_partner_id': partner_id.id})
            else:
                # Update partner with contact form
                vals['source'] = 'partner_form'
                partner_id = self.env['res.partner'].browse(int(res_partner_id))
                partner_id.message_follower_ids.sudo().unlink()
                partner_id.sudo().write(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super(ResPartnerForm, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                            toolbar=toolbar, submenu=submenu)
        if toolbar:
            doc = etree.XML(res['arch'])
            if self._context.get('request_id'):
                request_id = self.env['approval.request'].browse(self._context.get('request_id'))
                if request_id.request_status == 'pending':
                    for node_form in doc.xpath("//form"):
                        node_form.set("edit", "false")
                    res['arch'] = etree.tostring(doc)
        return res

    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = 0
