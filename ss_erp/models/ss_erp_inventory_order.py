# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class InventoryOrder(models.Model):
    _name = 'ss_erp.inventory.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Inventory Order'

    """
    Is an intermediate model use for transfer product between organization
    """

    company_id = fields.Many2one('res.company', string='会社', copy=False)
    name = fields.Char('番号', copy=False)
    # picking_type_id = fields.Many2one('stock.picking.type', 'オペレーションタイプ')
    organization_id = fields.Many2one('ss_erp.organization', '移動元組織')
    responsible_dept_id = fields.Many2one('ss_erp.responsible.department', '移動元管轄部門')
    location_id = fields.Many2one('stock.location', '移動元ロケーション')
    user_id = fields.Many2one('res.users', '担当者')
    scheduled_date = fields.Datetime('予定日', copy=False)
    shipping_method = fields.Selection([('transport', '配車（移動元）'), ('pick_up', '配車（移動先）'), ('outsourcing', '宅配')],
                                       default='transport', string='配送方法')
    state = fields.Selection([('draft', 'ドラフト'), ('waiting', '出荷待ち'), ('shipping', '積送中'),
                              ('done', '移動完了'), ('cancel', '取消済')], 'ステータス', default='draft', compute='_compute_state',
                             copy=False)
    inventory_order_line_ids = fields.One2many('ss_erp.inventory.order.line', 'order_id', string="オーダ明細")
    note = fields.Text('ノート')

    has_confirm = fields.Boolean(default=False, copy=False)
    has_cancel = fields.Boolean(default=False, copy=False)
    picking_count = fields.Integer(compute='_compute_picking_count')

    #
    @api.depends('state')
    def _compute_picking_count(self):
        for rec in self:
            sp = rec.env['stock.picking'].search([('x_inventory_order_id', '=', rec.id)])
            rec.picking_count = len(sp)

    #
    def show_stock_picking(self):
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        action['domain'] = [('x_inventory_order_id', '=', self.id)]
        return action

    #
    def cancel_state(self):
        self.has_cancel = True

    #
    @api.depends('has_confirm', 'inventory_order_line_ids.move_ids.state')
    def _compute_state(self):
        for rec in self:
            stock_picking_order = rec.env['stock.picking'].search([('x_inventory_order_id', '=', rec.id)])
            stp_state_all = stock_picking_order.mapped('state')
            stock_picking_to_virtual = rec.env['stock.picking'].search(
                [('x_inventory_order_id', '=', rec.id), ('location_dest_id_usage', '=', 'customer')])
            stp_vir = stock_picking_to_virtual.mapped('state')

            if rec.has_cancel:
                rec.state = 'cancel'
            else:
                if rec.has_confirm:
                    rec.state = 'waiting'
                    if all(s == 'done' for s in stp_state_all):
                        rec.state = 'done'
                    elif all(s == 'done' for s in stp_vir):
                        rec.state = 'shipping'
                        in_transfer = stock_picking_order - stock_picking_to_virtual
                        if in_transfer:
                            for it in in_transfer:
                                if it.state == 'confirmed':
                                    it.action_confirm()
                                    it.action_assign()
                else:
                    rec.state = 'draft'

    #
    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('ss_erp.inventory.order') or _('New')
        return super(InventoryOrder, self).create(vals)

    #
    def confirm_inventory_order(self):
        if self.inventory_order_line_ids:
            virtual_location = self.env['stock.location'].search([('usage', '=', 'customer')], limit=1)
            if not virtual_location:
                raise UserError(
                    _("Can't find virtual location. Please check stock.location again."))
            out_going = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
            in_coming = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)

            location_dest = self.inventory_order_line_ids.mapped('location_dest_id')
            for dest in location_dest:
                val = []
                for line in self.inventory_order_line_ids:
                    if dest.id == line.location_dest_id.id:
                        val.append(((0, 0, {
                            'x_inventory_order_line_id': line.id,
                            'product_id': line.product_id.id,
                            'product_uom_qty': line.product_uom_qty,
                            'product_uom': line.product_uom,
                            'name': self.name,
                            'state': 'confirmed',
                        })))
                    from_source_move = {
                        # 'state': 'confirmed',
                        'location_id': self.location_id.id,
                        'location_dest_id': virtual_location.id,
                        'picking_type_id': out_going.id,
                        'x_organization_id': self.organization_id.id,
                        'x_responsible_dept_id': self.responsible_dept_id.id,
                        'user_id': self.user_id.id,
                        'scheduled_date': self.scheduled_date,
                        'x_inventory_order_id': self.id,
                        'move_ids_without_package': val,
                    }

                    move_to_dest_location = {
                        # 'state': 'waiting',
                        'location_id': virtual_location.id,
                        'location_dest_id': dest.id,
                        'picking_type_id': in_coming.id,
                        'x_organization_id': line.organization_id.id,
                        'x_responsible_dept_id': line.responsible_dept_id.id,
                        'user_id': self.user_id.id,
                        'scheduled_date': self.scheduled_date,
                        'x_inventory_order_id': self.id,

                        'move_ids_without_package': val,
                    }
                out_transfer = self.env['stock.picking'].create(from_source_move)
                out_transfer.action_confirm()
                out_transfer.action_assign()

                self.env['stock.picking'].create(move_to_dest_location)

                self.has_confirm = True
        else:
            raise UserError(
                _("Please re check inventory order again."))


#
class InventoryOrderLine(models.Model):
    _name = 'ss_erp.inventory.order.line'
    _description = 'Inventory Order Line'

    company_id = fields.Many2one('res.company', string='会社', )
    order_id = fields.Many2one('ss_erp.inventory.order', 'オーダ参照', copy=False)
    move_ids = fields.One2many('stock.move', 'x_inventory_order_line_id')
    organization_id = fields.Many2one('ss_erp.organization', '移動先組織')
    responsible_dept_id = fields.Many2one('ss_erp.responsible.department', '移動元管轄部門')
    location_dest_id = fields.Many2one('stock.location', '移動先ロケーション')
    product_id = fields.Many2one('product.product', 'プロダクト')
    # lot_ids = fields.Many2many('stock.production.lot', string='シリアルナンバー')
    product_uom_qty = fields.Float('要求')
    product_uom = fields.Many2one('uom.uom', '単位')
    reserved_availability = fields.Float('引当済数量', compute='compute_reserved_availability')
    product_packaging = fields.Many2one('product.packaging', '荷姿')

    #
    @api.depends('move_ids.forecast_availability')
    def compute_reserved_availability(self):
        for rec in self:
            stock_move_out = rec.env['stock.move'].search([('x_inventory_order_line_id', '=', rec.id)], limit=1)
            if stock_move_out:
                rec.reserved_availability = stock_move_out.forecast_availability
            else:
                rec.reserved_availability = 0
