# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class OrganizationCategory(models.Model):
    _name = 'ss_erp.organization.category'
    _description = 'Organization'

    name = fields.Char(string='Category name')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        readonly=True, default=lambda self: self.env.company)
    sequence = fields.Integer("Sequence")
    active = fields.Boolean(
        default=True, help="If the active field is set to False, it will allow you to hide the payment terms without removing it.")
    hierarchy_number = fields.Integer("Hierarchy")
    organization_count = fields.Integer(
        string="Organization Count", compute="_compute_organization_count",
        compute_sudo=True
    )
    organization_ids = fields.One2many(
        "ss_erp.organization", "organization_category_id", string="Organizations")

    _sql_constraints = [
        ("name_uniq", "UNIQUE(name)", "Organization Category Name Should Be Unique!")
    ]

    @api.depends("organization_ids")
    def _compute_organization_count(self):
        for record in self:
            record.organization_count = len(record.organization_ids)

    def action_view_organizations(self):
        organization_ids = self.organization_ids
        action = self.env.ref('ss_erp_master.action_organizations')
        result = action.read()[0]
        result["context"] = {}
        organization_count = len(organization_ids)
        if organization_count != 1:
            result["domain"] = "[('organization_category_id', 'in', " + \
                str(self.ids) + ")]"
            return result
        res = self.env.ref('ss_erp_master.organization_view_form', False)
        result["views"] = [(res and res.id or False, "form")]
        result["res_id"] = organization_ids.id
        return result
