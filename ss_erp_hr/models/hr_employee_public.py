# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    # employee_number = fields.Char(readonly=True)

    organization_first = fields.Many2one(readonly=True)
    # department_jurisdiction_first = fields.Many2many('ss_erp.responsible.department', 'dept_juris_first_hr_public_rel', readonly=True)
    organization_second = fields.Many2one(readonly=True)
    # department_jurisdiction_second = fields.Many2many('ss_erp.responsible.department', 'dept_juris_second_hr_public_rel',readonly=True)
    organization_third = fields.Many2one(readonly=True)
    # department_jurisdiction_third = fields.Many2many('ss_erp.responsible.department', 'dept_juris_third_hr_public_rel',readonly=True)