from odoo import models, fields, _, api
from odoo.exceptions import ValidationError
from ..helpers import generate_random_string


class ResOrganization(models.Model):
    _name = "x.x_company_organization.res_org"
    _description = "Organization - Branch"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _inherits = {"res.partner": "partner_id"}

    # Odoo standard fields
    company_id = fields.Many2one(
        comodel_name="res.company", string="Company",
        ondelete="restrict", required=True, default=lambda self: self.env.company.id
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Contact", ondelete="restrict"
    )
    parent_id = fields.Many2one(
        comodel_name="x.x_company_organization.res_org", ondelete="restrict",
        index=True, auto_join=True, string="Parent Organization"
    )
    child_ids = fields.One2many(
        comodel_name="x.x_company_organization.res_org", inverse_name="parent_id",
        string="Contains Organizations"
    )
    active = fields.Boolean(
        string="Active", default=True
    )
    # Custom fields
    x_code = fields.Char(
        string="Organization Code", required=True, copy=False
    )
    x_organization_categ_id = fields.Many2one(
        comodel_name="x.x_company_organization.res_org_categ",
        string="Organization Category", ondelete="restrict",
        check_company=True, help="Category of this organization"
    )
    x_company_name = fields.Char(
        string="Company Name", related="company_id.name"
    )
    x_company_code = fields.Char(
        string="Company Code", related="company_id.x_code"
    )
    x_organization_manager_id = fields.Many2one(
        comodel_name="hr.employee", string="Person In Charge",
        readonly=True, check_company=True, help="Manager of this organization"
    )
    x_fax_number = fields.Char(
        string="Fax Number", size=20,
        help="Organization Fax Number."
    )
    x_employee_ids = fields.Many2many(
        comodel_name="hr.employee", string="Employee",
        check_company=True
    )
    x_sale_pic_ids = fields.Many2many(
        comodel_name="hr.employee", relation="sale_organization_rel",
        column1="org_id", column2="sale_user_id", string="Salesman In Charge",
        check_company=True, help="Person in charge of sales for this organization"
    )
    x_sale_tic_id = fields.Many2one(
        comodel_name="crm.team", string="Sales Team In Charge",
        check_company=True, help="Team in charge of sales for this organization"
    )
    x_sale_area = fields.Char(
        string="Sale Area", help="Sale area for this organization"
    )
    x_sale_stock_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse", string="Warehouse",
        ondelete="restrict", check_company=True,
        help="Sale products storage warehouse for this organization."
    )
    x_sale_stock_location_id = fields.Many2one(
        comodel_name="stock.location", string="Location",
        ondelete="restrict", check_company=True,
        help="Sale products storage location for this organization."
    )
    x_purchase_pic_ids = fields.Many2many(
        comodel_name="hr.employee", relation="purchase_organization_rel",
        column1="org_id", column2="purchase_user_id", string="Purchase Person In Charge",
        check_company=True, help="Person in charge of purchases for this organization"
    )
    x_purchase_tic_id = fields.Many2one(
        comodel_name="crm.team", string="Purchase Team In Charge",
        check_company=True, help="Team in charge of purchases for this organization"
    )
    x_purchase_area = fields.Char(
        string="Purchase Area", help="Purchase area for this organization"
    )
    x_purchase_stock_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse", string="Warehouse",
        ondelete="restrict", check_company=True,
        help="Purchase products storage warehouse for this organization."
    )
    x_purchase_stock_location_id = fields.Many2one(
        comodel_name="stock.location", string="Place Of Delivery",
        ondelete="restrict", domain="[('usage', 'in', ['view', 'internal'])]",
        help="Purchase products storage location for this organization."
    )

    @api.onchange("x_employee_ids")
    def _onchange_employee(self):
        self.update({
            "x_sale_pic_ids": [(5, 0, 0)],
            "x_purchase_pic_ids": [(5, 0, 0)]
        })
        if self.x_employee_ids:
            self._update_sale_person_in_charge()
            self._update_purchase_person_in_charge()

    def copy(self):
        return super(ResOrganization, self).copy({
            "name": "%s_%s" % (self.name, generate_random_string()),
            "x_code": generate_random_string()
        })

    def name_get(self):
        res = []
        for r in self:
            res.append((r.id, "%s (%s)" % (r.name, r.x_code)))
        return res

    def action_assign_manager(self):
        self.ensure_one()
        return True

    def _update_purchase_person_in_charge(self):
        self.ensure_one()
        purchases = self.x_employee_ids.filtered(
            lambda e: e.department_id.id == self.env.ref(
                "x_company_organization.department_purchase"
            ).id
        )
        purchase_pic = []
        for employee in purchases:
            purchase_pic += [(4, employee.id)]
        self.update({
            "x_purchase_pic_ids": purchase_pic
        })

    def _update_sale_person_in_charge(self):
        self.ensure_one()
        sales = self.x_employee_ids.filtered(
            lambda e: e.department_id.id == self.env.ref(
                "x_company_organization.department_sale"
            ).id
        )
        sale_pic = []
        for employee in sales:
            sale_pic += [(4, employee.id)]
        self.update({
            "x_sale_pic_ids": sale_pic
        })