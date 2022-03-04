# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from lxml import etree


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
        self.ensure_one()
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
                    line.price_unit = line.product_id.lst_price

                elif len(product_pricelist) == 1:
                    line.price_unit = product_pricelist.price_unit
                    line.x_pricelist = product_pricelist


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


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_approval_status = fields.Selection(related="order_id.approval_status", store=True)
    x_pricelist = fields.Many2one('ss_erp.product.price', string="価格リスト", index=True)
    x_expected_delivery_date = fields.Date("納期予定日")
    x_remarks = fields.Char("備考")
    price_unit = fields.Float('単価', required=True, digits='Product Price', default=0.0, store=True)

    x_is_required_x_pricelist = fields.Boolean(default=True)

    # date_order = fields.Many2one(related='order_id.date_order', string='Date Order', store=True, readonly=True)
    # organization_id = fields.Many2one(related='order_id.organization_id', string='Organization', store=True, readonly=True)
    #
    # @api.onchange('date_order', 'order_partner_id', 'company_id', 'organization_id')
    # def _onchange_get_line_product_price_list_from_date_order(self):

    # onchange auto caculate price unit from pricelist
    @api.onchange('product_id', 'product_uom_qty', 'product_uom')
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
                'price_unit': self.product_id.lst_price,
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
