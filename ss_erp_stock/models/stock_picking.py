# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_account_modify = fields.Boolean(
        "在庫仕訳訂正", index=True)
    x_dest_address_info = fields.Html("直送先住所")
    x_organization_id = fields.Many2one(
        'ss_erp.organization', string="移動元組織", domain="[('warehouse_id','!=',False)]")
    x_responsible_dept_id = fields.Many2one(
        'ss_erp.responsible.department', string="移動元管轄部門")
    x_responsible_dept_dest_id = fields.Many2one('ss_erp.responsible.department', string='移動先管轄部門')
    x_organization_dest_id = fields.Many2one('ss_erp.organization', string='移動先組織')
    x_mkt_user_id = fields.Many2one(
        'res.users', string="営業担当")
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

    x_construction_order_id = fields.Many2one('ss.erp.construction', string='工事オーダー')
    x_workorder_id = fields.Many2one('ss.erp.construction.workorder', string='作業オーダー')

    @api.depends("move_line_nosuggest_ids.product_id", "move_ids_without_package.product_id", "picking_type_id")
    def _compute_has_lot_ids(self):
        for r in self:
            products = r.move_line_nosuggest_ids.product_id | r.move_ids_without_package.product_id
            if products.filtered(lambda p: p.tracking == 'serial') and r.picking_type_id.code == 'incoming':
                r.has_lot_ids = True
            else:
                r.has_lot_ids = False

    @api.onchange('x_organization_id')
    def onchange_organization_id(self):
        if self.x_organization_id:
            return {'domain': {'picking_type_id': ['|', ('warehouse_id', '=', False),
                                                   ('warehouse_id', '=', self.x_organization_id.warehouse_id.id)],
                               }}


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_inventory_order_line_id = fields.Many2one(comodel_name='ss_erp.inventory.order.line', )


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    x_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='連絡先名',
        required=False)
