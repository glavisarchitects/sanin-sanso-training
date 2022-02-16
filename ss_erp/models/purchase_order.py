# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import html_translate

import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('x_mkt_user_id')
    def _compute_default_x_organization_id(self):
        for rec in self:
            employee_id = self.env['hr.employee'].search([('user_id','=',rec.x_mkt_user_id.id)], limit=1)
            if employee_id:
                rec.x_organization_id = employee_id.organization_first
            else:
                rec.x_organization_id = False

    @api.depends('x_mkt_user_id')
    def _compute_default_x_responsible_dept_id(self):
        for rec in self:
            employee_id = self.env['hr.employee'].search([('user_id', '=', rec.x_mkt_user_id.id)], limit=1)
            if employee_id:
                rec.x_responsible_dept_id = employee_id.department_jurisdiction_first[0]
            else:
                rec.x_responsible_dept_id = False

    x_bis_categ_id = fields.Many2one(
        'ss_erp.bis.category', string="取引区分", copy=True, index=True)
    x_rfq_issue_date = fields.Date("見積依頼日")
    x_po_issue_date = fields.Date("発注送付日")
    x_desired_delivery = fields.Selection([
        ('full', '完納希望'),
        ('separated', '分納可能'),
    ], string="希望納品", default='full', copy=True)
    x_dest_address_info = fields.Html("直送先情報")
    x_truck_number = fields.Char("車番")
    x_organization_id = fields.Many2one(
        'ss_erp.organization', string="担当組織", index=True, compute='_compute_default_x_organization_id')
    x_responsible_dept_id = fields.Many2one(
        'ss_erp.responsible.department', string="管轄部門", index=True, compute='_compute_default_x_responsible_dept_id')
    x_mkt_user_id = fields.Many2one(
        'res.users', string="営業担当者", index=True, default=lambda self: self.env.user)
    x_is_construction = fields.Boolean(
        "工事であるか", compute='_compute_show_construction', compute_sudo=True)
    x_construction_name = fields.Char("工事名称")
    x_construction_sopt = fields.Char("工事場所")
    x_construction_period_start = fields.Date(
        "予定工期開始")
    x_construction_period_end = fields.Date(
        "予定工期終了")
    x_supplies_check = fields.Selection([
        ('exist', 'あり'),
        ('no', 'なし'),
    ], string="支給品有無", default='no')
    x_supplies_info = fields.Char("支給品")
    x_construction_payment_term = fields.Char("支払条件", readonly=True, default=_(
        "工事支払条件（当社規定による、月末締切・翌月末支払）"))

    x_explanation_check = fields.Selection([
        ('exist', 'あり'),
        ('no', 'なし'),
    ], string="現説の有無", default='no')
    x_explanation_date = fields.Date("現説日付")
    x_explanation_spot = fields.Char("現説場所")
    x_construction_other = fields.Text("その他")
    x_construction_payment_cash = fields.Float("現金")
    x_construction_payment_bill = fields.Float("手形")
    x_construction_contract_notice = fields.Html(
        "工事契約における注記事項", copy=True, related='company_id.x_construction_contract_notice',store=True)
    x_construction_subcontract = fields.Html("下請工事の予定価格と見積期間",
                                             copy=True, related='company_id.x_construction_subcontract',store=True)
    is_dropshipping = fields.Boolean(
        '直送であるか', compute='_compute_is_dropshipping',)

    @api.depends('x_bis_categ_id')
    def _compute_show_construction(self):
        rec_construction_id = self.env.ref(
            "ss_erp.ss_erp_bis_category_data_0", raise_if_not_found=False)
        for rec in self:
            rec.x_is_construction = True if rec_construction_id and self.x_bis_categ_id and self.x_bis_categ_id.id == rec_construction_id.id else False

    @api.depends('order_line', 'order_line.product_id')
    def _compute_is_dropshipping(self):
        for record in self:
            record.is_dropshipping = False
            if record.order_line:
                route_id = self.env.ref(
                    'stock_dropshipping.route_drop_shipping', raise_if_not_found=False)
                record.is_dropshipping = True if route_id in record.mapped(
                    'product_id').mapped('route_ids') else False

    def action_rfq_send(self):
        res = super(PurchaseOrder, self).action_rfq_send()
        if self.env.context.get('send_rfq', False):
            res['context'].update({
                'default_template_id': self.env.ref("ss_erp.email_template_edi_purchase_quotation").id
            })
            res['context'].update({
                'partner_email_field': 'x_email_quote_request',
            })
        else:
            res['context'].update({
                'default_template_id': self.env.ref("ss_erp.email_template_edi_purchase_order").id
            })
            res['context'].update({
                'partner_email_field': 'x_email_purchase',
            })
        return res

    def print_quotation(self):
        res = super(PurchaseOrder, self).print_quotation()
        if self.x_is_construction:
            return self.env.ref('action_report_estimate_request').report_action(self)
        else:
            return self.env.ref('action_report_purchasequotation').report_action(self)

    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res.update({
            'user_id': self.user_id and self.user_id.id or False,
            'x_dest_address_info': self.x_dest_address_info,
            'x_organization_id': self.x_organization_id and self.x_organization_id.id or False,
            'x_responsible_dept_id': self.x_responsible_dept_id and self.x_responsible_dept_id.id or False,
            'x_mkt_user_id': self.x_mkt_user_id and self.x_mkt_user_id.id or False,
        })
        return res


