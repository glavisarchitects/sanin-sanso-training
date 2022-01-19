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

    @api.constrains("name","company_id")
    def _check_name(self):
        for record in self:
            organization_category_count = self.env['ss_erp.organization.category'].search_count(
                [('name', '=', record.name),('company_id','=',record.company_id.id)])
            if organization_category_count > 1:
                raise ValidationError(_("同じ組織カテゴリが存在しています"))

    @api.constrains("hierarchy_number","company_id")
    def _check_hierarchy_number(self):
        for record in self:
            organization_category_count = self.env['ss_erp.organization.category'].search_count(
                [('hierarchy_number', '=', record.hierarchy_number),('company_id','=',record.company_id.id)])
            if organization_category_count > 1:
                raise ValidationError(_("同じ階層番号が存在しています。"))
            if record.hierarchy_number <= 0:
                raise ValidationError(_("階層番号は入力してください。"))

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
