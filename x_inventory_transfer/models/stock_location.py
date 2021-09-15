from odoo import fields,models

class StockLocation(models.Model):
    _name = "stock.location"
    _inherit = ["stock.location", "x.x_company_organization.org_mixin"]



class StockWarehouse(models.Model):
    _name ="stock.warehouse"

    _inherit = ["stock.warehouse", "x.x_company_organization.org_mixin"]



