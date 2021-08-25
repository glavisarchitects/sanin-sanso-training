from odoo import api, models, fields, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    x_movement_type = fields.Selection([
        ('within', 'In the base'),
        ('between', 'Between bases'),
        ('disposal', 'Disposal'),
    ], string='Movement type', default='within',
        track_visibility='onchange', copy=False,translate = True)
    x_remark = fields.Selection([
        ('internal', 'Internal Transfer'),
        ('direct', 'Direct Transfer')],
        string='Remark', default='internal', track_visibility='onchange', copy=False,translate = True)
    x_shipping_slip_number = fields.Char(string='Shipping slip number',translate = True)
    x_inbound_slip_number = fields.Char(string='Inbound slip number',translate = True)

    x_shipping_methods = fields.Selection([
        ('internal', 'Delivered from the move source -> The move destination.'),
        ('dispatch', 'Go to the destination -> The destination to pick up')],
        string='Dispatch Method', track_visibility='onchange', copy=False, translate = True)


    x_dispatch_ids = fields.Many2many('x.dispatch.method',string ="Shipping method ", readonly=False, translate = True)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('stock.picking')
        res = super(StockPicking, self).create(vals)

        return res

    @api.depends('move_ids_without_package')
    def _compute_max_line_sequence(self):
        for picking in self:
            picking.max_line_sequence = (
                    max(picking.mapped('move_ids_without_package.sequence') or
                        [0]) + 1
            )

    max_line_sequence = fields.Integer(string='Max sequence in lines',
                                       compute='_compute_max_line_sequence')


    def _reset_sequence(self):
        for rec in self:
            current_sequence = 1
            for line in rec.move_ids_without_package:
                line.x_detail_no = current_sequence
                current_sequence += 1




    class XDispatchMethod(models.Model):
        _name= 'x.dispatch.method'
        _description= "Dispatch Method"


        name = fields.Char(string='Name')
        description = fields.Char(string='Description')













