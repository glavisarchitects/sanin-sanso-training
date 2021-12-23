# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class InstructionOrder(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'ss_erp.instruction.order'
    _description = 'Instruction Slip'


    name = fields.Char(default='New', string='Inventory reference')
    sequence = fields.Integer(string='Sequence')
    accounting_date = fields.Date("Accounting Date", required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)
    date = fields.Date(string='Inventory adjustment date', default=lambda self: fields.Date.context_today(self), required=True)
    exhausted = fields.Boolean(string='Include out-of-stock products')
    # line_ids = fields.One2many('stock.inventory.line', 'inventory_id', string='Inventory')
    location_ids = fields.Many2many(
        'stock.location', 'location_instruction_rel', 'location_id', 'restruction_id',
        string='Location'
        )
    # move_ids = fields.One2many('stock.move', 'inventory_id', string='Generated inventory movement')
    prefill_counted_quantity = fields.Selection([
        ('counted', '手持在庫をデフォルト提案'),
        ('zero', 'ゼロをデフォルト提案'),
    ],string='Inventory quantity')
    product_ids = fields.Many2many(
        'product.product', 'product_instruction_rel', 'product_id', 'instruction_id',
        string='Product'
        )
    start_empty = fields.Boolean(string='Empty inventory')
    state = fields.Selection([
        ('draft', 'ドラフト'),
        ('cancel', '取消済'),
        ('confirm', '進行中'),
        ('waiting', '承認待ち'),
        ('approval', '承認依頼中'),
        ('approved', '承認済み'),
        ('done', '検証済'),
    ], string='State')

    organization_id = fields.Many2one('ss_erp.organization', string='Organization name', required=True)
    type_id = fields.Many2one('product.template', string='Inventory type', required=True)
    stock_inventory_id = fields.Many2one('stock.inventory', string='Inventory slip number')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'ss_erp.instruction.order.name') or _('New')
        result = super(InstructionOrder, self).create(vals)
        return result

    @api.constrains('accounting_date')
    def _check_accounting_date(self):
        for record in self:
            if record.accounting_date > fields.Date.today():
                raise ValidationError(
                    _("The starting date cannot be after the ending date. The estimated shipping date cannot be set earlier than the current date")
                )
            elif record.accounting_date < record.date:
                raise ValidationError(
                    _("Please select a date after the scheduled inventory date for the accounting date.")
                )

    def display_action(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'name': _('Instruction slip details'),
            'res_model': 'ss_erp.instruction.order.line',
        }
        context = {
            'default_is_editable': True,
            'default_order_id': self.id,
        }
        # Define domains and context
        domain = [
            ('order_id', '=', self.id),
        ]
        action['view_id'] = self.env.ref('ss_erp.ss_erp_instruction_order_line_tree').id
        action['context'] = context
        action['domain'] = domain
        return action

    def search_action(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'name': _('Instruction slip details'),
            'res_model': 'ss_erp.instruction.order.line',
        }
        context = {
            'default_is_editable': True,
            'default_order_id': self.id,
        }
        # Define domains and context
        domain = [
            ('order_id', '=', self.id),
            ('organization_id', '=', self.organization_id.id)
        ]
        action['view_id'] = self.env.ref('ss_erp.ss_erp_instruction_order_line_tree').id
        action['context'] = context
        action['domain'] = domain
        return action

    def action_create_inventory(self):
        if not self.stock_inventory_id:
            inventory_data = {
                'name': self.env['ir.sequence'].next_by_code('stock.inventory.name'),
                'company_id': self.company_id.id,
                'organization_id': self.organization_id.id,
                'type_id': self.type_id.id,
                'accounting_date': self.accounting_date,
                'prefill_counted_quantity': self.prefill_counted_quantity,
                'instruction_order_id': self.id
            }
            line_ids = []
            lines = self.env['ss_erp.instruction.order.line'].search([('order_id', '=', self.id)])
            for line in lines:
                line_data = {
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'location_id': line.location_id.id,
                    'prod_lot_id': line.prod_lot_id.id,
                    'inventory_order_line_id': line.id,
                    # 'product_qty': line.product_qty,
                }
                line_ids.append((0, 0, line_data))
            inventory_data['line_ids'] = line_ids
            stock_inventory_id = self.env['stock.inventory'].create(inventory_data)
            self.stock_inventory_id = stock_inventory_id
