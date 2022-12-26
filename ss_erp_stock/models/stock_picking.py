# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_account_modify = fields.Boolean(
        "在庫仕訳訂正", index=True)
    x_dest_address_info = fields.Html("直送先住所")
    x_organization_id = fields.Many2one(
        'ss_erp.organization', string="移動元組織",
        domain=lambda self: [('id', 'in', self._login_user_organization_id())],
        default=lambda self: self._get_default_x_organization_id())
    x_responsible_dept_id = fields.Many2one(
        'ss_erp.responsible.department', string="移動元管轄部門",
        default=lambda self: self._get_default_x_responsible_dept_id())

    def _login_user_organization_id(self):
        organization_ids = self.env.user.organization_ids.filtered(lambda x: x.warehouse_id != False)
        return organization_ids.ids if organization_ids else False

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

    x_responsible_dept_dest_id = fields.Many2one('ss_erp.responsible.department', string='移動先管轄部門', store=True)
    x_organization_dest_id = fields.Many2one('ss_erp.organization', string='移動先組織', store=True)
    x_mkt_user_id = fields.Many2one(
        'res.users', string="営業担当", store=True)
    x_shipping_method = fields.Selection(related='x_inventory_order_id.shipping_method')
    # TODO
    x_import_id = fields.Char("Capture ID", copy=False)
    x_inspection_user_id = fields.Many2one(
        comodel_name='res.users',
        string='良品検査担当者名',
        required=False)

    x_inspection_exist = fields.Boolean(
        string='良品検査実施有無',
        default=False)

    has_lot_ids = fields.Boolean(
        'Has Serial Numbers', compute='_compute_has_lot_ids')

    x_inventory_order_id = fields.Many2one('ss_erp.inventory.order')

    @api.depends("move_line_nosuggest_ids.product_id", "move_ids_without_package.product_id", "picking_type_id")
    def _compute_has_lot_ids(self):
        for r in self:
            products = r.move_line_nosuggest_ids.product_id | r.move_ids_without_package.product_id
            if products.filtered(lambda p: p.tracking == 'serial') and r.picking_type_id.code == 'incoming':
                r.has_lot_ids = True
            else:
                r.has_lot_ids = False

    required_responsible_dept_id = fields.Boolean(compute='_compute_responsible_dept_id')

    x_inventory_journal_date = fields.Datetime('在庫仕訳日')

    @api.depends('x_organization_id')
    def _compute_responsible_dept_id(self):
        for rec in self:
            rec.required_responsible_dept_id = True
            if rec.x_organization_id.organization_code == '00120':
                rec.required_responsible_dept_id = False

    @api.onchange('x_organization_id')
    def onchange_organization_id(self):
        if self.x_organization_id:
            self.update({
                'picking_type_id': False,
                'location_id': False,
                'location_dest_id': False,
            })
            for move in self.move_ids_without_package:
                move.update({
                    'x_organization_id': self.x_organization_id
                })
            return {'domain': {'picking_type_id': ['|', ('warehouse_id', '=', False),
                                                   ('warehouse_id', '=', self.x_organization_id.warehouse_id.id)],
                               }}

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        if self.picking_type_code == 'incoming':
            return {'domain': {'location_dest_id': ['|', ('usage', '=', 'internal'), ('x_stored_location', '=', True), (
                'id', 'child_of', self.picking_type_id.warehouse_id.view_location_id.id)]}}
        elif self.picking_type_code == 'outgoing':
            return {'domain': {'location_id': ['|', ('usage', '=', 'internal'), ('x_stored_location', '=', True), (
                'id', 'child_of', self.picking_type_id.warehouse_id.view_location_id.id)]}}
        elif self.picking_type_code == 'internal':
            return {'domain': {
                'location_dest_id': [('id', 'child_of', self.picking_type_id.warehouse_id.view_location_id.id),
                                     ('scrap_location', '=', False), ('return_location', '=', False)],
                'location_id': [('id', 'child_of', self.picking_type_id.warehouse_id.view_location_id.id),
                                ('scrap_location', '=', False), ('return_location', '=', False)]}}
        elif self.picking_type_code == 'mrp_operation':
            return {'domain': {'location_id': [('usage', '=', 'internal'), (
                'id', 'child_of', self.picking_type_id.warehouse_id.view_location_id.id)]}
                    }

    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        for picking in self:
            if picking.state != 'draft':
                # for some reason moves added after state = 'done' won't save group_id, reference if added in
                # "stock_move.default_get()"
                picking.move_ids_without_package.write({
                    'x_organization_id': picking.x_organization_id.id,
                    'x_responsible_dept_id': picking.x_responsible_dept_id.id,
                    'x_responsible_user_id': picking.user_id.id
                })
        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_inventory_order_line_id = fields.Many2one(comodel_name='ss_erp.inventory.order.line', )


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    x_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='連絡先名',
        required=False)
