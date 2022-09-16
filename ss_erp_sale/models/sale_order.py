# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from lxml import etree
from odoo.tools.float_utils import float_round
import math

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_organization_id = fields.Many2one('ss_erp.organization', string="販売組織", copy=True,
                                        default=lambda self: self._get_default_x_organization_id())
    x_responsible_dept_id = fields.Many2one('ss_erp.responsible.department', string="管轄部門", copy=True,
                                            default=lambda self: self._get_default_x_responsible_dept_id())
    x_no_approval_required_flag = fields.Boolean('承認不要フラグ?')
    approval_status = fields.Selection(
        string='承認済み区分',
        selection=[('out_of_process', '未承認'),
                   ('in_process', '承認中'),
                   ('approved', '承認済み')],copy=False,
        required=False, default='out_of_process')

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

    def action_confirm(self):
        if not self.x_no_approval_required_flag and self.approval_status != 'approved':
            raise UserError(_("確認する前に、承認フローを完了してください・"))
        res = super(SaleOrder, self).action_confirm()

        if self.picking_ids:
            self.picking_ids.update({
                'user_id': self.user_id and self.user_id.id or False,
                'x_organization_id': self.x_organization_id and self.x_organization_id.id or False,
                'x_responsible_dept_id': self.x_responsible_dept_id and self.x_responsible_dept_id.id or False,}
            )
        return res

    def _prepare_confirmation_values(self):
        return {
            'state': 'sale',
        }

    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel', 'sent'])
        orders.update({
            'approval_status': 'out_of_process',
        })

        super(SaleOrder, orders).action_draft()

    def write(self, vals):
        return super(SaleOrder, self).write(vals)

    def action_quotation_sent(self):
        if self.filtered(lambda so: not so.x_no_approval_required_flag and so.approval_status == 'in_process'):
            raise UserError(_('未承認のため、見積を送信済みとしてマークすることができません。'))
        super(SaleOrder, self).action_quotation_sent()

    #
    @api.onchange('date_order', 'partner_id', 'company_id', 'x_organization_id')
    def _onchange_get_line_product_price_list_from_date_order(self):
        if self.order_line:
            for line in self.order_line:
                organization_id = self.x_organization_id.id
                partner_id = self.partner_id.id
                company_id = self.company_id.id
                date_order = self.date_order

                product_pricelist = self.env['ss_erp.product.price'].search(
                    ['&', '&', '&', '&', '&',
                     '|', ('organization_id', '=', organization_id), ('organization_id', '=', False),
                     '|', ('uom_id', '=', line.product_uom.id), ('uom_id', '=', False),
                     '|', ('product_uom_qty_min', '<=', line.product_uom_qty), ('product_uom_qty_min', '=', 0),
                     '|', ('product_uom_qty_max', '>=', line.product_uom_qty), ('product_uom_qty_max', '=', 0),
                     '|', ('partner_id', '=', partner_id), ('partner_id', '=', False),
                     ('company_id', '=', company_id), ('product_id', '=', line.product_id.id),
                     ('start_date', '<=', date_order), ('end_date', '>=', date_order)])
                if len(product_pricelist) == 0:
                    # Can't find ss_erp_pricelist match with input condition
                    line.x_pricelist = False
                    line.x_is_required_x_pricelist = False
                    line.price_unit = line.product_id.list_price

                elif len(product_pricelist) == 1:
                    line.price_unit = product_pricelist.price_unit
                    line.x_pricelist = product_pricelist

    @api.onchange('x_organization_id')
    def _onchange_x_organization_id(self):
        if self.x_organization_id:
            self.warehouse_id = self.x_organization_id.warehouse_id.id

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super(SaleOrder, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                     toolbar=toolbar, submenu=submenu)
        # print(self._context())
        if toolbar:
            doc = etree.XML(res['arch'])
            if self._context.get('request_id'):
                sale_order = self.env['sale.order'].browse(self._context.get('sale_quotation'))
                if sale_order.approval_status == 'pending':
                    for node_form in doc.xpath("//form"):
                        node_form.set("edit", "false")
                    res['arch'] = etree.tostring(doc)
        return res

    # cancel sale order if apply for approval
    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        approval_sale = self.env['approval.request'].search([('x_sale_order_ids', 'in', self.id),
                                                             ('request_status', 'not in',['cancel', 'refuse'])])
        if approval_sale:
            for approval in approval_sale:
                if len(approval.x_sale_order_ids) > 1:
                    message = '見積番号%sが見積操作で取消されたため、承認申請から削除されました。' % self.name
                    approval.sudo().write({'x_sale_order_ids': [(3, self.id)]})
                    approval.message_post(body=_(message))
                else:
                    approval.sudo().update({
                        'request_status': 'cancel',
                    })
                    approval.message_post(body=_('承認申請の見積が見積操作で取消されたため、承認申請を取消しました。'))
        return res

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({
            'x_organization_id': self.x_organization_id.id,
            'x_responsible_dept_id': self.x_responsible_dept_id.id,
            'x_responsible_user_id': self.user_id.id,
            'x_mkt_user_id': self.user_id.id,
        })
        return invoice_vals

    # svf region
    def send_data_svf_cloud(self):
        self.env['svf.cloud.config'].sudo().get_access_token()

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_approval_status = fields.Selection(related="order_id.approval_status", store=True)
    x_pricelist = fields.Many2one('ss_erp.product.price', string="価格リスト", index=True)
    x_expected_delivery_date = fields.Date("納期予定日")
    x_remarks = fields.Char("備考")
    price_unit = fields.Float('単価', required=True, digits='Product Price', default=0.0, store=True)

    x_is_required_x_pricelist = fields.Boolean(default=True)
    x_pricelist_list = fields.Many2many('ss_erp.product.price', compute='_compute_x_pricelist_list')

    @api.depends('product_id', 'product_uom_qty', 'product_uom', 'x_alternative_unit_id', 'x_conversion_quantity')
    def _compute_x_pricelist_list(self):
        organization_id = self.order_id.x_organization_id.id
        partner_id = self.order_id.partner_id.id
        company_id = self.order_id.company_id.id
        date_order = self.order_id.date_order

        product_pricelist = self.env['ss_erp.product.price'].search(
            ['&', '&', '&', '&', '&',
             '|', ('organization_id', '=', organization_id), ('organization_id', '=', False),
             '|', ('uom_id', '=', self.product_uom.id), ('uom_id', '=', False),
             '|', ('product_uom_qty_min', '<=', self.product_uom_qty), ('product_uom_qty_min', '=', 0),
             '|', ('product_uom_qty_max', '>=', self.product_uom_qty), ('product_uom_qty_max', '=', 0),
             '|', ('partner_id', '=', partner_id), ('partner_id', '=', False),
             ('company_id', '=', company_id), ('product_id', '=', self.product_id.id),
             ('start_date', '<=', date_order), ('end_date', '>=', date_order)])

        product_pricelist2 = self.env['ss_erp.product.price'].search(
            ['&', '&', '&', '&', '&',
             '|', ('organization_id', '=', organization_id), ('organization_id', '=', False),
             '|', ('uom_id', '=', self.x_alternative_unit_id.id), ('uom_id', '=', False),
             '|', ('product_uom_qty_min', '<=', self.x_conversion_quantity), ('product_uom_qty_min', '=', 0),
             '|', ('product_uom_qty_max', '>=', self.x_conversion_quantity), ('product_uom_qty_max', '=', 0),
             '|', ('partner_id', '=', partner_id), ('partner_id', '=', False),
             ('company_id', '=', company_id), ('product_id', '=', self.product_id.id),
             ('start_date', '<=', date_order), ('end_date', '>=', date_order)])

        self.x_pricelist_list = product_pricelist+product_pricelist2

    # DUNK-F-001_開発設計書_C001_ガス換算
    x_conversion_quantity = fields.Float('換算数量', store=True)
    x_product_alternative_unit_ids = fields.One2many('uom.uom', compute='get_x_product_alternative_unit_ids')
    x_alternative_unit_id = fields.Many2one('uom.uom', '代替単位')

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
        medium_classification_code = self.env['ir.config_parameter'].sudo().get_param(
            'ss_erp_product_medium_class_for_convert')

        if not medium_classification_code:
            raise UserError(
                "プロダクト中分類の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。（ss_erp_product_medium_class_for_convert）")
        medium_classification_code.split(",")
        if self.x_alternative_unit_id and self.product_id.x_medium_classification_id.medium_classification_code in medium_classification_code:
            conversion_quantity = float_round(conversion_quantity, precision_digits=2)
        else:
            if self.x_alternative_unit_id.id == self.env.ref('uom.product_uom_kgm').id:
                conversion_quantity = int(conversion_quantity)
                # self.product_uom_qty = float_round(self.product_uom_qty, precision_digits=0)
            else:
                conversion_quantity = math.floor(conversion_quantity * 100)/100

        self.x_conversion_quantity = conversion_quantity


    # onchange auto caculate price unit from pricelist
    @api.onchange('product_id', 'product_uom_qty', 'product_uom', 'x_alternative_unit_id','x_conversion_quantity')
    def _onchange_get_product_price_list(self):
        organization_id = self.order_id.x_organization_id.id
        partner_id = self.order_id.partner_id.id
        company_id = self.order_id.company_id.id
        date_order = self.order_id.date_order

        product_pricelist = self.env['ss_erp.product.price'].search(
            ['&', '&', '&', '&', '&',
             '|', ('organization_id', '=', organization_id), ('organization_id', '=', False),
             '|', ('uom_id', '=', self.product_uom.id), ('uom_id', '=', False),
             '|', ('product_uom_qty_min', '<=', self.product_uom_qty), ('product_uom_qty_min', '=', 0),
             '|', ('product_uom_qty_max', '>=', self.product_uom_qty), ('product_uom_qty_max', '=', 0),
             '|', ('partner_id', '=', partner_id), ('partner_id', '=', False),
             ('company_id', '=', company_id), ('product_id', '=', self.product_id.id),
             ('start_date', '<=', date_order), ('end_date', '>=', date_order)])

        # set False for pricelist core
        self.order_id.pricelist_id = False
        if len(product_pricelist) == 0:
            # Can't find ss_erp_pricelist match with input condition
            self.update({
                'x_pricelist': False,
                'price_unit': self.product_id.list_price,
                'x_is_required_x_pricelist': False
            })

        elif len(product_pricelist) == 1:
            self.price_unit = product_pricelist.price_unit
            self.x_pricelist = product_pricelist
        else:
            self.x_pricelist = False
            self.x_is_required_x_pricelist = True

            # return {'domain': {'x_pricelist': [('id', 'in', product_pricelist.ids)]
            #                    }}

    @api.onchange('x_pricelist')
    def _compute_price_unit(self):
        if self.x_pricelist:
            self.write({
                'price_unit': self.product_id.list_price,
            })
        else:
            self.write({
                'price_unit': self.x_pricelist.price_unit,
            })

    @api.constrains('x_expected_delivery_date')
    def expected_delivery_date_constrains(self):
        for rec in self:
            if rec.x_expected_delivery_date:
                current_date = fields.Date.today()
                if rec.x_expected_delivery_date < current_date:
                    raise ValidationError(_("納期は現在より過去の日付は設定できません。"))

    @api.model
    def create(self, vals):
        if self.x_pricelist:
            vals.update({
                'price_unit': self.x_pricelist.price_unit,
            })
        res = super(SaleOrderLine, self).create(vals)
        return res

    def write(self, vals):
        if self.x_pricelist:
            vals.update({
                'price_unit': self.x_pricelist.price_unit,
            })
        return super(SaleOrderLine, self).write(vals)
