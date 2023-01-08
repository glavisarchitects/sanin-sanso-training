# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # employee_number = fields.Char(string='従業員番号', )
    #
    # organization_first = fields.Many2one('ss_erp.organization', string='第一組織', )
    # department_jurisdiction_first = fields.Many2many('ss_erp.responsible.department', 'dept_juris_first_rel',
    #                                                  string='第一組織管轄部門', )
    # organization_second = fields.Many2one('ss_erp.organization', string='第二組織')
    # department_jurisdiction_second = fields.Many2many('ss_erp.responsible.department', 'dept_juris_second_rel',
    #                                                   string='第二組織管轄部門')
    # organization_third = fields.Many2one('ss_erp.organization', string='第三組織')
    # department_jurisdiction_third = fields.Many2many('ss_erp.responsible.department', 'dept_juris_third_rel',
    #                                                  string='第三組織管轄部門')

    @api.constrains("employee_number", )
    def _check_same_employee_number(self):
        for r in self:
            employee_count = r.env['hr.employee'].search_count([('employee_number', '=', r.employee_number)])
            if employee_count > 1:
                raise ValidationError(_("同じ従業員番号が存在しています"))

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

    # # Check Jurisdiction
    # @api.constrains("department_jurisdiction_first", "department_jurisdiction_second", "department_jurisdiction_third")
    # def _check_same_jurisdiction(self):
    #     for r in self:
    #         if r.department_jurisdiction_first.filtered(lambda m: m.id in r.department_jurisdiction_second.ids) or \
    #                 r.department_jurisdiction_second.filtered(lambda m: m.id in r.department_jurisdiction_third.ids) or \
    #                 r.department_jurisdiction_third.filtered(lambda m: m.id in r.department_jurisdiction_first.ids):
    #             raise ValidationError(_('同一の管轄部門が選択されています'))


    @api.model
    def create(self, vals):
        employee = super(HrEmployee, self).create(vals)
        employee._update_user_organizations()
        employee._update_user_dept()
        return employee

    def _update_user_organizations(self):
        self.ensure_one()
        organizations = self.organization_first | self.organization_second | self.organization_third
        organization_ids = organizations.ids
        if not organization_ids or not self.user_id:
            return
        return self.user_id.write({
            "organization_ids": [(6, 0, organization_ids)]
        })

    def _update_user_dept(self):
        self.ensure_one()
        dept = self.department_jurisdiction_first | self.department_jurisdiction_second | self.department_jurisdiction_third
        dept_ids = dept.ids
        if not dept_ids or not self.user_id:
            return
        return self.user_id.write({
            "dep_ids": [(6, 0, dept_ids)]
        })

    def write(self, vals):
        res = super(HrEmployee, self).write(vals)
        for r in self:
            r._update_user_organizations()
        return res
