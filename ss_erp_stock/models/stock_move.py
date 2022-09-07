from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    inventory_order_line_id = fields.Many2one('ss_erp.inventory.order.line', string="移動オーダ明細")
    product_packaging = fields.Many2one(string='パッケージ', related='inventory_order_line_id.product_packaging', store=True)
    x_organization_id = fields.Many2one('ss_erp.organization', related='picking_id.x_organization_id',
                                      string='組織名', store=True)

    x_responsible_dept_id = fields.Many2one('ss_erp.responsible.department',
                                                 related='picking_id.x_responsible_dept_id', string='管轄部門', store=True)


