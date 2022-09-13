# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import html_translate
from odoo.tools.float_utils import float_round

import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_organization_id = fields.Many2one(
        'ss_erp.organization', string="担当組織", index=True,
        default=lambda self: self._get_default_x_organization_id())
    x_responsible_dept_id = fields.Many2one(
        'ss_erp.responsible.department', string="管轄部門", index=True,
        default=lambda self: self._get_default_x_responsible_dept_id())

    def _get_default_x_organization_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id.organization_first
        else:
            return False

    def _get_default_x_responsible_dept_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id and employee_id.department_jurisdiction_first:
            return employee_id.department_jurisdiction_first[0]
        else:
            return False

    # x_bis_categ_id = fields.Many2one(
    #     'ss_erp.bis.category', string="取引区分", copy=True, index=True)
    x_bis_categ_id = fields.Selection(
        string='取引区分',
        selection=[('gas_material', 'ガス・器材'),
                   ('construction', '工事'), ],
        required=False, )

    x_rfq_issue_date = fields.Date("見積依頼日")
    x_po_issue_date = fields.Date("発注送付日")
    x_desired_delivery = fields.Selection([
        ('full', '完納希望'),
        ('separated', '分納可能'),
    ], string="希望納品", default='full', copy=True)
    x_dest_address_info = fields.Html("直送先情報")
    x_truck_number = fields.Char("車番")

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
        "工事契約における注記事項", copy=True, related='company_id.x_construction_contract_notice', store=True)
    x_construction_subcontract = fields.Html("下請工事の予定価格と見積期間",
                                             copy=True, related='company_id.x_construction_subcontract', store=True)

    @api.onchange('x_organization_id')
    def _onchange_x_organization_id(self):
        if self.x_organization_id:
            self.picking_type_id = self.x_organization_id.warehouse_id.in_type_id.id

    @api.depends('x_bis_categ_id')
    def _compute_show_construction(self):
        for rec in self:
            rec.x_is_construction = True if self.x_bis_categ_id == 'construction' else False

    def action_rfq_send(self):
        res = super(PurchaseOrder, self).action_rfq_send()
        if self.env.context.get('send_rfq', False):
            res['context'].update({
                'default_template_id': self.env.ref("ss_erp_purchase.email_template_edi_purchase_quotation").id
            })
            res['context'].update({
                'partner_email_field': 'x_email_quote_request',
            })
        else:
            res['context'].update({
                'default_template_id': self.env.ref("ss_erp_purchase.email_template_edi_purchase_order").id
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

    #
    def button_cancel(self):
        """ also cancel approval related"""
        res = super(PurchaseOrder, self).button_cancel()
        approval_purchase = self.env['approval.request'].search([('x_purchase_order_ids', 'in', self.id),
                                                                 ('request_status', 'not in', ['cancel', 'refuse'])])
        if approval_purchase:
            for approval in approval_purchase:
                if len(approval.x_purchase_order_ids) > 1:
                    message = '見積依頼伝票%sが見積操作で取消されたため、承認申請から削除されました。' % self.name
                    approval.sudo().write({'x_purchase_order_ids': [(3, self.id)]})
                    approval.message_post(body=message)
                else:
                    approval.sudo().update({
                        'request_status': 'cancel',
                    })
                    approval.message_post(body=_('承認申請の見積依頼伝票が見積依頼操作で取消されたため、承認申請を取消しました。'))
        return res

    # 07092022 , x_payment_type related partner and x_responsible_user_id related user_id of po
    def _prepare_invoice(self):
        head_office_organization = self.env['ss_erp.organization'].search([('organization_code', '=', '00000')],
                                                                          limit=1)
        business_department = self.env['ss_erp.responsible.department'].search([('name', '=', '業務')], limit=1)
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        invoice_vals.update({
            'x_responsible_user_id': self.user_id or False,
            'x_payment_type': self.partner_id.x_payment_type,
            'x_organization_id': head_office_organization.id,
            'x_responsible_dept_id': business_department.id,
        })
        return invoice_vals


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_fixed_cost = fields.Float("仕入定価")

    # DUNK-F-001_開発設計書_C001_ガス換算
    x_conversion_quantity = fields.Float('換算数量', store=True)
    x_product_alternative_unit_ids = fields.One2many('uom.uom', compute='get_x_product_alternative_unit_ids')
    x_alternative_unit_id = fields.Many2one('uom.uom', '代替単位')

    #
    @api.depends('product_id')
    def get_x_product_alternative_unit_ids(self):
        for rec in self:
            rec.x_product_alternative_unit_ids = rec.product_id.x_product_unit_measure_ids.mapped('alternative_uom_id')

    # onchange auto caculate x_conversion_quantity
    @api.onchange('x_alternative_unit_id', 'product_uom_qty')
    def _onchange_get_x_conversion_quantity(self):
        product_uom_alternative = self.product_id.x_product_unit_measure_ids.filtered(
            lambda pum: pum.alternative_uom_id == self.x_alternative_unit_id)
        conversion_quantity = product_uom_alternative.converted_value * self.product_uom_qty

        # C001_ガス換算
        if self.x_alternative_unit_id and self.product_id.x_medium_classification_id.id in [
            self.env.ref('ss_erp_product_template.product_medium_classification_propane').id,
            self.env.ref('ss_erp_product_template.product_medium_classification_butan1').id,
            self.env.ref('ss_erp_product_template.product_medium_classification_butan2').id,
            self.env.ref('ss_erp_product_template.product_medium_classification_industry_propane').id,
            self.env.ref('ss_erp_product_template.product_medium_classification_industry_butan').id]:
            conversion_quantity = float_round(conversion_quantity, precision_digits=2)
        else:
            if self.x_alternative_unit_id.id == self.env.ref('uom.product_uom_kgm').id:
                conversion_quantity = int(conversion_quantity)
            else:
                conversion_quantity = round(conversion_quantity, 2)

        self.x_conversion_quantity = conversion_quantity

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.x_fixed_cost = self.product_id and self.product_id.x_fixed_cost
