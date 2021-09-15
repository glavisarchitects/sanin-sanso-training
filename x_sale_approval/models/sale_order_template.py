from odoo import fields, models, api


class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    x_order_date = fields.Date(string='Order Date', required=False)
    x_contract_start = fields.Date(string='Contract Dateline', require=False)
    x_contract_end = fields.Date(string='Contract Dateline', require=False)
