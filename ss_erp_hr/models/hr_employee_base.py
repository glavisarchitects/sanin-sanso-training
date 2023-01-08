# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrEmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    employee_number = fields.Char(string='従業員番号', )

    organization_first = fields.Many2one('ss_erp.organization', string='第一組織', )
    department_jurisdiction_first = fields.Many2many('ss_erp.responsible.department', 'dept_juris_first_rel',
                                                     string='第一組織管轄部門', )
    organization_second = fields.Many2one('ss_erp.organization', string='第二組織')
    department_jurisdiction_second = fields.Many2many('ss_erp.responsible.department', 'dept_juris_second_rel',
                                                      string='第二組織管轄部門')
    organization_third = fields.Many2one('ss_erp.organization', string='第三組織')
    department_jurisdiction_third = fields.Many2many('ss_erp.responsible.department', 'dept_juris_third_rel',
                                                     string='第三組織管轄部門')

    department_jurisdiction_first_char = fields.Char(compute='_compute_dep_jfc', store=True, string='第一組織管轄部門', )
    department_jurisdiction_second_char = fields.Char(compute='_compute_dep_jsc', store=True, string='第二組織管轄部門', )
    department_jurisdiction_third_char = fields.Char(compute='_compute_dep_jtc', store=True, string='第三組織管轄部門', )

    @api.depends('department_jurisdiction_first')
    def _compute_dep_jfc(self):
        for rec in self:
            rec.department_jurisdiction_first_char = ''
            if rec.department_jurisdiction_first:
                for dep in rec.department_jurisdiction_first:
                    rec.department_jurisdiction_first_char += '「' + dep.name + '」'

    @api.depends('department_jurisdiction_second')
    def _compute_dep_jsc(self):
        for rec in self:
            rec.department_jurisdiction_second_char = ''
            if rec.department_jurisdiction_second:
                for dep in rec.department_jurisdiction_second:
                    rec.department_jurisdiction_second_char += '「' + dep.name + '」'

    @api.depends('department_jurisdiction_third')
    def _compute_dep_jtc(self):
        for rec in self:
            rec.department_jurisdiction_third_char = ''
            if rec.department_jurisdiction_third:
                for dep in rec.department_jurisdiction_third:
                    rec.department_jurisdiction_third_char += '「' + dep.name + '」'
