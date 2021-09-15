import string
from odoo import models, fields
from ..helpers import generate_random_string



class EmployeeBase(models.AbstractModel):
    _name = "hr.employee.base"
    _inherit = ["hr.employee.base", "x.x_company_organization.org_mixin"]

    x_company_name = fields.Char(
        string="Company Name", related="company_id.name"
    )
    x_company_code = fields.Char(
        string="Company Code", related="company_id.x_code"
    )
    x_organization_name = fields.Char(
        string="Organization Name", related="x_organization_id.name",
    )
    x_organization_code = fields.Char(
        string="Organization Code", related="x_organization_id.x_code",
    )
    x_crm_team_id = fields.Many2one(
        comodel_name="crm.team", string="Responsible Team",
        check_company=True
    )

    def name_get(self):
        res = []
        for r in self:
            name = "%s (%s)" % (r.name, r.job_title) if r.job_title else r.name
            res.append((r.id, name))
        return res


class Employee(models.Model):
    _inherit = "hr.employee"

    x_employee_number = fields.Char(
        string="Employee Number", size=10, required=True, copy=False,
        help="Unique Number for this employee!"
    )

    _sql_constraints = [
        (
            "employee_number_company_uniq",
            "UNIQUE(x_employee_number, company_id)",
            "Employee Number should be unique in company!"
         )
    ]

    def copy(self):
        return super(Employee, self).copy({
            "x_employee_number": generate_random_string(seq=string.digits, lengh=10)
        })

    def _sync_user(self, user, employee_has_image=False):
        res = super(Employee, self)._sync_user(user, employee_has_image)
        res.update({
            "x_organization_id": user.x_organization_id and user.x_organization_id.id
        })
        return res
