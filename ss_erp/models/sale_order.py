# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, date


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_organization_id = fields.Many2one('ss_erp.organization', string="販売組織", copy=False)
    x_responsible_dept_id = fields.Many2one('ss_erp.responsible.department', string="管轄部門", copy=False)
    x_no_approval_required_flag = fields.Boolean('承認不要フラグ?')
    approval_status = fields.Selection(
        string='承認済み区分',
        selection=[('out_of_process', '未承認'),
                   ('in_process', '承認中'),
                   ('approved', '承認済み')],
        required=False, default='out_of_process')

    def action_confirm(self):
        if not self.x_no_approval_required_flag and self.approval_status != 'approved':
            raise UserError(_("Please complete approval flow before change to order"))
        return super(SaleOrder, self).action_confirm()

    def action_quotation_sent(self):
        if self.filtered(lambda so: not so.x_no_approval_required_flag and so.approval_status != 'approved'):
            raise UserError(_('Only approved orders can be marked as sent directly.'))
        super(SaleOrder, self).action_quotation_sent()

    #
    @api.onchange('date_order', 'partner_id', 'company_id')
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
                # print("###########################", product_pricelist)

                # set False for pricelist core
                self.order_id.pricelist_id = False
                if len(product_pricelist) == 0:
                    # Can't find ss_erp_pricelist match with input condition
                    line.x_pricelist = False
                    line.x_is_required_x_pricelist = False
                    line.price_unit = line.product_id.lst_price

                elif len(product_pricelist) == 1:
                    line.price_unit = product_pricelist.price_unit
                    line.x_pricelist = product_pricelist


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_pricelist = fields.Many2one('ss_erp.product.price', string="価格リスト", index=True)
    x_expected_delivery_date = fields.Date("納期予定日")
    x_remarks = fields.Char("備考")

    x_is_required_x_pricelist = fields.Boolean(default=True)

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

        self.x_is_required_x_pricelist = True

        # set False for pricelist core
        self.order_id.pricelist_id = False
        if len(product_pricelist) == 0:
            # Can't find ss_erp_pricelist match with input condition
            self.x_pricelist = False
            self.price_unit = self.product_id.lst_price
            self.x_is_required_x_pricelist = False

        elif len(product_pricelist) == 1:

            self.price_unit = product_pricelist.price_unit
            self.x_pricelist = product_pricelist

        return {'domain': {'x_pricelist': [('id', 'in', product_pricelist.ids)]
                           }}

    @api.onchange('x_pricelist')
    def _onchange_x_pricelist(self):
        if self.x_pricelist:
            self.price_unit = self.x_pricelist.price_unit