# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_number = fields.Char(string='Employee Number', required=True)

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
        "Same employee number exists!"
    )]

    # @api.constrains('organization_first', 'organization_second', 'organization_third')
    # def _check_organization_constraint(self):
    #     for record in self:
    #         if record.organization_first.id != record.organization_second.id and\
    #                 record.organization_second.id != record.organization_third.id:
    #             return True
    #         else:
    #             raise ValidationError(_('The same organization is selected'))

    # @api.constrains('department_jurisdiction_first', 'department_jurisdiction_second', 'department_jurisdiction_third')
    # def _check_department_jurisdiction_constraint(self):
    #     for employee in self:
    #         print('*************employee***********',employee)
    #         for record in employee:
    #             print('*************employee***********',record)
    #             if record.department_jurisdiction_first.id != record.department_jurisdiction_second.id != \
    #                     record.department_jurisdiction_third.id:
    #                 return True
    #             else:
    #                 raise ValidationError(_('Same jurisdiction selected'))
