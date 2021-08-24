from odoo import models, fields
from ..helpers import generate_random_string

class ResOrganizationCategory(models.Model):
    _name = "x.x_company_organization.res_org_categ"
    _description = "Organization Category"

    name = fields.Char(
        "Organization Category", required=True, copy=False,
        help="Name of organization category"
    )
    company_id = fields.Many2one(
        "res.company", string="Company", required=True,
        default=lambda self: self.env.company.id
    )
    active = fields.Boolean(
        string="Active", default=True
    )
    x_company_name = fields.Char(
        string="Company Name", related="company_id.name"
    )
    x_company_code = fields.Char(
        string="Company Code", related="company_id.x_code"
    )

    _sql_constraints = [
        ("name_uniq", "UNIQUE(name)", "Organization Category Name Should Be Unique!")
    ]

    def copy(self):
        return super(ResOrganizationCategory, self).copy({
            "name": "%s_%s" % (self.name, generate_random_string())
        })
