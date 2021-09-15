from odoo import api, models, fields, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking","x.x_company_organization.org_mixin"]

    x_movement_type = fields.Selection([
        ('within', 'In the base'),
        ('between', 'Between bases'),
        ('disposal', 'Disposal'),
    ], string='Movement type', default='within',
        track_visibility='onchange', copy=False, translate=True)
    x_remark = fields.Selection([
        ('internal', 'Internal Transfer'),
        ('direct', 'Direct Transfer')],
        string='Remark', default='internal', track_visibility='onchange', copy=False, translate=True)
    x_shipping_slip_number = fields.Char(string='Shipping slip number', translate=True)
    x_inbound_slip_number = fields.Char(string='Inbound slip number', translate=True)

    x_shipping_methods = fields.Selection([
        ('internal', 'Delivered from the move source -> The move destination.'),
        ('dispatch', 'Go to the destination -> The destination to pick up')],
        string='Dispatch Method', track_visibility='onchange', copy=False, translate=True)

    x_dispatch_ids = fields.Many2many('x.dispatch.method', string="Shipping method ", readonly=False, translate=True)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('transfer_internal_sequence')
        res = super(StockPicking, self).create(vals)

        return res

    def prepare_processing(self):
        self.write({
            'state': 'draft'
        })

    def _reset_sequence(self):
        for rec in self:
            current_sequence = 1
            for line in rec.move_ids_without_package:
                line.sequence = current_sequence
                current_sequence += 1


    def copy(self, default=None):
        return super(StockPicking,
                     self.with_context(keep_line_sequence=True)).copy(default)


    def button_validate(self):
        return super(StockPicking,
                     self.with_context(keep_line_sequence=True)
                     ).button_validate()


    @api.depends('move_ids_without_package')
    def _compute_max_line_sequence(self):
        """Allow to know the highest sequence entered in move lines.
        Then we add 1 to this value for the next sequence, this value is
        passed to the context of the o2m field in the view.
        So when we create new move line, the sequence is automatically
        incremented by 1. (max_sequence + 1)
        """
        for picking in self:
            picking.line_sequence = (
                    max(picking.mapped('move_ids_without_package.sequence') or
                        [0])
            )

    line_sequence = fields.Integer(string='Sequence in lines',
                                       compute='_compute_max_line_sequence')

class XDispatchMethod(models.Model):
    _name = "x.dispatch.method"
    _description = "Dispatch Method"

    name = fields.Char(string='Name')
    description = fields.Char(string='Description')
