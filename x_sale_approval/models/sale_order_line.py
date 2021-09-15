# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    # _inherit = ["sale.order.line", "x.x_company_organization.org_mixin"]
    _inherit = ["sale.order.line"]

    x_shipping_information = fields.Char(string='配送情報', required=False)

    x_campaign = fields.Many2one(
        comodel_name='product.pricelist',
        string='キャンペーン',
        required=False,

        # TODO: Filter pricelist in branch
        # domain="[('field_id.name', 'in', 'message_ids')]"
    )

    x_expected_delivery_date = fields.Date(string='納期予定日', default=fields.Date.today, required=True,
                                           help='Expected delivery date')

    def _update_price_unit(self):
        """ For a given pricelist, return price for a given product """
        price_unit = self.product_id.pricelist_id.get_product_price(self.product_id, self.product_uom_qty,
                                                                    self.order_id.partner_id,
                                                                    uom_id=self.product_uom.id)
        return price_unit

    @api.onchange('x_campaign')
    def _onchange_x_campaign(self):
        # TODO: confirm price list in branch or company
        # TODO: get price unit in price list
        # TODO: update price list by discount

        product = self.product_id.with_context(
            partner=self.order_id.partner_id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.x_campaign.id,
            uom=self.product_uom.id
        )
        price_unit = product.price

        # price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),
        #                                                                      self.product_id.taxes_id, self.tax_id,
        #                                                                      self.company_id)

        if self.x_campaign.discount_policy == 'without_discount' and price_unit:
            discount = max(0, (self.product_id.price - price_unit) * 100 / price_unit)
        else:
            discount = 0
        self.write({'price_unit': price_unit, 'discount': discount})

        # self.order_id.show_update_pricelist = False

    def _is_none(self, string):
        if string:
            return string + ' '
        return ''

    @api.onchange('product_id')
    def _onchange_product_id(self):
        #
        # # TODO: confirm pricelist display [ branch or company ]
        # # price list for product or price list for sale order
        # self.x_campaign = self.product_id.pricelist_id.name
        #
        # # address
        # address = self._is_none(self.order_id.partner_id.street) \
        #           + self._is_none(self.order_id.partner_id.city) \
        #           + self._is_none(self.order_id.partner_id.state_id.name) \
        #           + self._is_none(self.order_id.partner_id.zip) \
        #           + self._is_none(self.order_id.partner_id.country_id.name)
        #
        # self.x_shipping_information = self._is_none(address)
        #
        # self.x_campaign = self.env['product.pricelist'].search([]).filtered(
        #     lambda prl: prl.item_ids.product_id == self.product_id)
        today = datetime.now()
        price_list_ids = self.env['product.pricelist'].search([])
        price_list = []
        for pl in price_list_ids:
            if self.product_id:
                exist = False
                for pd in pl.item_ids:
                    date_start = pd.date_start if pd.date_start else datetime(1900, 1, 1)
                    date_end = pd.date_end if pd.date_end else datetime(9999, 12, 30)
                    if pd.applied_on == '3_global' and date_start <= today <= date_end:
                        price_list.append(pl.id)
                        exist = True
                        break
                    if pd.applied_on == '2_product_category' and self.product_id.categ_id == pd.categ_id and date_start <= today <= date_end:
                        price_list.append(pl.id)
                        exist = True
                        break
                    if pd.product_tmpl_id and pd.product_tmpl_id.id == self.product_id.id and date_start <= today <= date_end:
                        price_list.append(pl.id)
                        exist = True
                        break
            else:
                price_list.append(pl.id)
        res = {}
        res['domain'] = {'x_campaign': [('id', 'in', price_list)]}
        return res
