from odoo import models, fields


class ResUsers(models.Model):
    _inherit = "res.users"

    x_organization_id = fields.Many2one(
        "x.x_company_organization.res_org", string="Organization",
        help="Working organization of this user"
    )
    x_employee_number = fields.Char(
        related="employee_id.x_employee_number"
    )
