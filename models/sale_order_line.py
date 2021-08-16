from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    campaign_id = fields.Many2one("product.pricelist", string="Campaign")
    supervise_group_id = fields.Many2one("res.groups", string="Supervise")
