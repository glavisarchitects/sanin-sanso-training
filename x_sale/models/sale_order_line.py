from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = ["sale.order.line"]
    _description = "sanin-sanso sale order line"

    x_shipping_information = fields.Char(string='配送情報', required=False)
    x_campaign = fields.Char(string='キャンペーン', required=False)
    x_expected_delivery_date = fields.Char(string='納期予定日', default=fields.Date.today, required=True)
