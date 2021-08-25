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




    class XDispatchMethod(models.Model):
        _name= 'x.dispatch.method'
        _description= "Dispatch Method"


        name = fields.Char(string='Name')
        description = fields.Char(string='Description')













