# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class MrpUnbuild(models.Model):
    _inherit = 'mrp.unbuild'

    x_organization_id = fields.Many2one('ss_erp.organization', store=True,
                                        default=lambda self: self._get_default_x_organization_id(), string='担当組織')
    x_responsible_dept_id = fields.Many2one('ss_erp.responsible.department',
                                            default=lambda self: self._get_default_x_responsible_dept_id(),
                                            string='管轄部門')
    x_organization_root_location_id = fields.Many2one('stock.location', related='x_organization_id.warehouse_id.view_location_id')

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

    def _generate_move_from_existing_move(self, move, factor, location_id, location_dest_id):
        return self.env['stock.move'].create({
            'name': self.name,
            'date': self.create_date,
            'product_id': move.product_id.id,
            'product_uom_qty': move.product_uom_qty * factor,
            'product_uom': move.product_uom.id,
            'procure_method': 'make_to_stock',
            'location_dest_id': location_dest_id.id,
            'location_id': location_id.id,
            'warehouse_id': location_dest_id.get_warehouse().id,
            'unbuild_id': self.id,
            'company_id': move.company_id.id,
            'x_organization_id': self.x_organization_id.id,
            'x_responsible_dept_id': self.x_responsible_dept_id.id,
            'x_responsible_user_id': self.env.user.id,
        })

    def _generate_move_from_bom_line(self, product, product_uom, quantity, bom_line_id=False, byproduct_id=False):
        product_prod_location = product.with_company(self.company_id).property_stock_production
        location_id = bom_line_id and product_prod_location or self.location_id
        location_dest_id = bom_line_id and self.location_dest_id or product_prod_location
        warehouse = location_dest_id.get_warehouse()
        return self.env['stock.move'].create({
            'name': self.name,
            'date': self.create_date,
            'bom_line_id': bom_line_id,
            'byproduct_id': byproduct_id,
            'product_id': product.id,
            'product_uom_qty': quantity,
            'product_uom': product_uom.id,
            'procure_method': 'make_to_stock',
            'location_dest_id': location_dest_id.id,
            'location_id': location_id.id,
            'warehouse_id': warehouse.id,
            'unbuild_id': self.id,
            'company_id': self.company_id.id,
            'x_organization_id': self.x_organization_id.id,
            'x_responsible_dept_id': self.x_responsible_dept_id.id,
            'x_responsible_user_id': self.env.user.id,
        })

