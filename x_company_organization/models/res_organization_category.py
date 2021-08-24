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
    x_organization_ids = fields.One2many(
        comodel_name="x.x_company_organization.res_org",
        inverse_name="x_organization_categ_id", string="Organizations",
    )
    x_organization_count = fields.Integer(
        string="Organization Count", compute="_compute_organization_count",
        compute_sudo=True
    )

    _sql_constraints = [
        ("name_uniq", "UNIQUE(name)", "Organization Category Name Should Be Unique!")
    ]

    def _compute_organization_count(self):
        datas = self.env["x.x_company_organization.res_org"].read_group(
            [("x_organization_categ_id", "in", self.ids)],
            ["x_organization_categ_id"],
            ["x_organization_categ_id"]
        )
        mapped_data = dict([(data["x_organization_categ_id"][0],
                             data["x_organization_categ_id_count"])
                            for data in datas])
        for r in self:
            r.x_organization_count = mapped_data.get(r.id, 0)

    def copy(self):
        return super(ResOrganizationCategory, self).copy({
            "name": "%s_%s" % (self.name, generate_random_string())
        })

    def action_view_organizations(self):
        organization_ids = self.x_organization_ids
        action = self.env.ref('x_company_organization.action_organizations')
        result = action.read()[0]
        result["context"] = {}
        organization_count = len(organization_ids)
        if organization_count != 1:
            result["domain"] = "[('x_organization_categ_id', 'in', " + str(self.ids) + ")]"
        elif organization_count == 1:
            res = self.env.ref('x_company_organization.res_organization_view_form', False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = organization_ids.id
        return result
