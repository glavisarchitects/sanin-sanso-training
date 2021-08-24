from odoo import models, fields


class OrganizationMixin(models.AbstractModel):
    _name = "x.x_company_organization.org_mixin"
    _description = "Organization Mixin"

    x_organization_id = fields.Many2one(
        comodel_name="x.x_company_organization.res_org", string="Organization",
        default=lambda self: self.env.user.x_organization_id and self.env.user.x_organization_id.id,
        help="Organization which create this record."
    )
