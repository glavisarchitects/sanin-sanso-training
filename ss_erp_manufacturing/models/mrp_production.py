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

    def write(self, vals):
        if not self.check_access_rights('write', raise_exception=False):
            return False
        res = super(MrpProduction, self).write(vals)
        for production in self:
            if production.state != 'draft':
                # for some reason moves added after state = 'done' won't save group_id, reference if added in
                # "stock_move.default_get()"
                production.move_raw_ids.write({
                    'x_organization_id': production.x_organization_id.id,
                    'x_responsible_dept_id': production.x_responsible_dept_id.id,
                    'x_responsible_user_id': production.user_id.id
                })
                production.move_finished_ids.write({
                    'x_organization_id': production.x_organization_id.id,
                    'x_responsible_dept_id': production.x_responsible_dept_id.id,
                    'x_responsible_user_id': production.user_id.id
                })
        return res
