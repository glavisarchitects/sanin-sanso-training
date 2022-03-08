# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    x_organization_id = fields.Many2one('ss_erp.organization', string="販売組織",readonly=True)
    x_responsible_dept_id = fields.Many2one('ss_erp.responsible.department', string="管轄部門", readonly=True)

    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['x_organization_id'] = ", s.x_organization_id as x_organization_id"
        fields['x_responsible_dept_id'] = ", s.x_responsible_dept_id as x_responsible_dept_id"
        groupby += ', s.x_organization_id, s.x_responsible_dept_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)

