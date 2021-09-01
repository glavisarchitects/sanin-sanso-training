# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    # _inherit = ["sale.order.line", "x.x_company_organization.org_mixin"]
    _inherit = ["sale.order.line"]

    x_shipping_information = fields.Char(string='配送情報', required=False)
    x_campaign = fields.Char(string='キャンペーン', required=False)

    x_expected_delivery_date = fields.Date(string='納期予定日', default=fields.Date.today, required=True, help='Expected delivery date')


    @api.onchange("product_id")
    def _onchange_product_id(self):
        self.x_shipping_information = self.order_id.partner_id.street \
                                      + ' - ' + self.order_id.partner_id.city \
                                      + ' - ' + self.order_id.partner_id.state_id.name \
                                      + ' - ' + self.order_id.partner_id.zip \
                                      + ' - ' + self.order_id.partner_id.country_id.name

        # price list for product or price list for sale order
        self.x_campaign = self.product_id.pricelist_id.name or self.order_id.pricelist_id.name

