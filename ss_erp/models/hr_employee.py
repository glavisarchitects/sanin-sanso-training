# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_number = fields.Char(string='Employee Number', )

    organization_first = fields.Many2one('ss_erp.organization', string='Organization First', required=True)
    department_jurisdiction_first = fields.Many2many('ss_erp.responsible.department', 'dept_juris_first_rel',
                                                     string='Department Jurisdiction First', required=True)
    organization_second = fields.Many2one('ss_erp.organization', string='Organization Second')
    department_jurisdiction_second = fields.Many2many('ss_erp.responsible.department', 'dept_juris_second_rel',
                                                      string='Department Jurisdiction Second')
    organization_third = fields.Many2one('ss_erp.organization', string='Organization Third')
    department_jurisdiction_third = fields.Many2many('ss_erp.responsible.department', 'dept_juris_third_rel',
                                                     string='Department Jurisdiction Third')

    _sql_constraints = [(
        "employee_number_uniq",
        "UNIQUE(employee_number)",
        "同じ社員番号が存在しています"
    )]

    # Check Organization
    @api.constrains("organization_first", "organization_second", "organization_third")
    def _check_same_organization(self):
        for r in self:
            if r.organization_second or r.organization_third:
                if r.organization_first.id == r.organization_second.id or \
                        r.organization_second.id == r.organization_third.id or \
                        r.organization_third.id == r.organization_first.id:
                    raise ValidationError(_("同一の組織が選択されています"))

            if not r.organization_second and r.organization_third:
                raise ValidationError(_("第二組織が選択されていません"))

    # Check Jurisdiction
    @api.constrains("department_jurisdiction_first", "department_jurisdiction_second", "department_jurisdiction_third")
    def _check_same_jurisdiction(self):
        for r in self:
            if r.department_jurisdiction_first.filtered(lambda m: m.id in r.department_jurisdiction_second.ids) or \
                    r.department_jurisdiction_second.filtered(lambda m: m.id in r.department_jurisdiction_third.ids) or \
                    r.department_jurisdiction_third.filtered(lambda m: m.id in r.department_jurisdiction_first.ids):
                raise ValidationError(_('Same jurisdiction selected'))
