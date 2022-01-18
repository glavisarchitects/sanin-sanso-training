# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class OrganizationCategory(models.Model):
    _name = 'ss_erp.organization.category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Organization category'

    name = fields.Char(string='Category name')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=False)
    sequence = fields.Integer("Sequence")
    active = fields.Boolean(
        default=True, )
    hierarchy_number = fields.Integer("Hierarchy", )
    organization_count = fields.Integer(
        string="Organization Count", compute="_compute_organization_count",
        compute_sudo=True
    )
    organization_ids = fields.One2many(
        "ss_erp.organization", "organization_category_id", string="Organizations")

    _sql_constraints = [
        ("name_uniq", "UNIQUE(name)", "Organization Category Name Should Be Unique!"),
        ("name_hierarchy_number", "UNIQUE(hierarchy_number)", "階層番号は既に登録されています。"),
        ('check_hierarchy_number', 'CHECK(hierarchy_number > 0)', '階層番号は0より入力してください。'),
    ]

    @api.depends("organization_ids")
    def _compute_organization_count(self):
        for record in self:
            record.organization_count = len(record.organization_ids)

    def action_view_organizations(self):
        organization_ids = self.organization_ids
        action = self.env.ref('ss_erp.action_organizations')
        result = action.read()[0]
        result["context"] = {}
        organization_count = len(organization_ids)
        if organization_count != 1:
            result["domain"] = "[('organization_category_id', 'in', " + \
                               str(self.ids) + ")]"
            return result
        res = self.env.ref('ss_erp.organization_view_form', False)
        result["views"] = [(res and res.id or False, "form")]
        result["res_id"] = organization_ids.id
        return result

    def unlink(self):
        for record in self:
            if self.env['ss_erp.organization'].search([('organization_category_id', '=', record.id)]):
                raise UserError(_(
                    'You can not delete organization category as other records still reference it. However, you can archive it.'))
        return super(OrganizationCategory, self).unlink()
