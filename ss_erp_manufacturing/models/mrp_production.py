# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    x_organization_id = fields.Many2one('ss_erp.organization', store=True,
                                        default=lambda self: self._get_default_x_organization_id(), string='担当組織')
    x_responsible_dept_id = fields.Many2one('ss_erp.responsible.department',
                                            default=lambda self: self._get_default_x_responsible_dept_id(),
                                            string='管轄部門')

    def _get_default_x_organization_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id.organization_first
        else:
            return False

    def _get_default_x_responsible_dept_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id and employee_id.department_jurisdiction_first:
            return employee_id.department_jurisdiction_first
        else:
            return False

    def _get_move_raw_values(self, product_id, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        data = super()._get_move_raw_values(product_id, product_uom_qty, product_uom, operation_id=False, bom_line=False)
        data.update({
            'x_organization_id': self.x_organization_id.id,
            'x_responsible_dept_id': self.x_responsible_dept_id.id
        })
        return data

    def _get_move_finished_values(self, product_id, product_uom_qty, product_uom, operation_id=False, byproduct_id=False):
        data = super()._get_move_finished_values(product_id, product_uom_qty, product_uom, operation_id=False, byproduct_id=False)
        data.update({
            'x_organization_id': self.x_organization_id.id,
            'x_responsible_dept_id': self.x_responsible_dept_id.id
        })
        return data

