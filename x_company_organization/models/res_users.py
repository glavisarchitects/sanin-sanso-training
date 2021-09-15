from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    x_organization_id = fields.Many2one(
        "x.x_company_organization.res_org", string="Organization",
        help="Working organization of this user"
    )


class ResUsers(models.Model):
    _inherit = "res.users"

    x_employee_number = fields.Char(
        related="employee_id.x_employee_number"
    )
