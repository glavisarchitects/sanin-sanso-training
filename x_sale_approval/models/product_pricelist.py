from odoo import fields, models, api


class ProductPriceList(models.Model):
    _name = "product.pricelist"

    # TODO confirm: using inherit or relationship

    # _inherit = ["product.pricelist", "x.x_company_organization.org_mixin"]
    _inherit = ["product.pricelist"]
    org_ids = fields.Many2many('x.x_company_organization.res_org', string='Branch Name')
