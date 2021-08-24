from odoo import models, _
from odoo.exceptions import ValidationError


class Department(models.Model):
    _inherit = "hr.department"

    def unlink(self):
        sale_department = self.env.ref("x_company_organization.department_sale")
        purchase_department = self.env.ref("x_company_organization.department_sale")
        if self.filtered(lambda d: d.id in (sale_department | purchase_department).ids):
            raise ValidationError(_("Base Department can not be deleted!"))
        return super(Department, self).unlink()

    def write(self, vals):
        sale_department = self.env.ref("x_company_organization.department_sale")
        purchase_department = self.env.ref("x_company_organization.department_sale")
        if self.filtered(lambda d: d.id in (sale_department | purchase_department).ids) and\
            vals.get("active"):
            raise ValidationError(_("Base Department can not be in-activated!"))
        return super(Department, self).write(vals)
