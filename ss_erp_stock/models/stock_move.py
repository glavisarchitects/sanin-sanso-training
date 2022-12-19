from odoo import models, fields, api
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    inventory_order_line_id = fields.Many2one('ss_erp.inventory.order.line', string="移動オーダ明細")
    instruction_order_id = fields.Many2one('ss_erp.instruction.order', string="棚卸計画")
    instruction_order_line_id = fields.Many2one('ss_erp.instruction.order.line', string="棚卸計画明細")

    product_packaging = fields.Many2one(string='パッケージ', related='inventory_order_line_id.product_packaging', store=True)
    x_organization_id = fields.Many2one('ss_erp.organization', default=lambda self: self.picking_id.x_organization_id,
                                        string='組織名', store=True)

    x_responsible_dept_id = fields.Many2one('ss_erp.responsible.department',
                                            default=lambda self: self.picking_id.x_responsible_dept_id.id,
                                            string='管轄部門', store=True)

    x_responsible_user_id = fields.Many2one('res.users', default=lambda self: self.picking_id.user_id,
                                            string='業務担当', store=True)

    lpgas_adjustment = fields.Boolean(string='', default=False)

    is_stored_location_transfer = fields.Boolean(compute='_computed_is_stored_location_transfer')

    @api.depends('location_id', 'location_dest_id')
    def _computed_is_stored_location_transfer(self):
        for rec in self:
            if (rec.location_id.x_stored_location and rec.location_dest_id.usage == 'internal') or (
                    rec.location_dest_id.x_stored_location and rec.location_id.usage == 'internal'):
                rec.is_stored_location_transfer = True
            else:
                rec.is_stored_location_transfer = False

    def _is_in(self):
        if self.lpgas_adjustment:
            if self.location_id.usage == 'inventory':
                return True
            else:
                return False
        elif self.is_stored_location_transfer:
            if (self.location_id.type != 'internal' and self.location_dest_id.x_stored_location) or (
                    self.location_id.x_stored_location and self.location_dest_id.type == 'internal'):
                return True
            else:
                return False
        else:
            return super()._is_in()

    def _is_out(self):
        if self.lpgas_adjustment:
            if self.location_dest_id.usage == 'inventory':
                return True
            else:
                return False
        elif self.is_stored_location_transfer:
            if (self.location_id.type == 'internal' and self.location_dest_id.x_stored_location) or (
                    self.location_id.x_stored_location and self.location_dest_id.type != 'internal'):
                return True
            else:
                return False
        else:
            return super()._is_out()
