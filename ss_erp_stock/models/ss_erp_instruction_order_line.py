# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from datetime import datetime

class InstructionOrderLine(models.Model):
    _name = 'ss_erp.instruction.order.line'
    _description = '指示伝票明細'

    @api.model
    def _domain_location_id(self):
        return "[('usage', 'in', ['internal', 'transit'])]"

    categ_id = fields.Many2one('product.category', string='プロダクトカテゴリ')
    company_id = fields.Many2one('res.company', string='会社')
    difference_qty = fields.Float(string='差異', compute='_compute_difference', readonly=True)
    display_name = fields.Char(string='表示名')
    inventory_date = fields.Datetime(string='在庫調整日')
    inventory_id = fields.Many2one('stock.inventory', string='在庫')
    is_editable = fields.Boolean(string='編集可能か')
    location_id = fields.Many2one('stock.location', string='ロケーション', required=True,
                                  domain=lambda self: self._domain_location_id())
    outdated = fields.Boolean(string='数量が古くなっています')
    package_id = fields.Many2one('stock.quant.package', string='梱包')
    partner_id = fields.Many2one('res.partner', string='オーナー')
    prod_lot_id = fields.Many2one('stock.production.lot', string='ロット/シリアル番号')
    product_id = fields.Many2one('product.product', string='プロダクト', required=True)
    product_qty = fields.Float(string='棚卸数量')
    product_tracking = fields.Selection(string='追跡', related='product_id.tracking')
    product_uom_id = fields.Many2one('uom.uom', string='プロダクト単位', required=True)
    state = fields.Selection(string='ステータス', related='inventory_id.state')
    theoretical_qty = fields.Float(readonly=True, string='理論数量')
    order_id = fields.Many2one('ss_erp.instruction.order', string='オーダ参照', required=True, ondelete='cascade')
    organization_id = fields.Many2one('ss_erp.organization', related='order_id.organization_id',
                                      string='組織名')
    # type_id = fields.Many2one('product.template', related='order_id.type_id', string='棚卸種別')
    stock_inventory_line_id = fields.Many2one('stock.inventory.line', string='棚卸明細')
    product_cost = fields.Float(string='単価')

    def init(self):
        field = self.env['ir.model.fields'].search(
            [('model_id.model', '=', 'ss_erp.instruction.order.line'), ('name', '=', 'product_qty')], limit=1)
        if field and field.ttype == 'many2one':
            self._cr.execute('alter table ss_erp_instruction_order_line drop column product_qty;')

    @api.depends('product_qty', 'theoretical_qty')
    def _compute_difference(self):
        for line in self:
            line.difference_qty = line.product_qty - line.theoretical_qty

    @api.onchange('product_id', 'location_id', 'product_uom_id', 'prod_lot_id', 'partner_id', 'package_id')
    def _onchange_quantity_context(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
        if self.product_id and self.location_id and self.product_id.uom_id.category_id == self.product_uom_id.category_id:  # TDE FIXME: last part added because crash
            theoretical_qty = self.product_id.get_theoretical_quantity(
                self.product_id.id,
                self.location_id.id,
                lot_id=self.prod_lot_id.id,
                package_id=self.package_id.id,
                owner_id=self.partner_id.id,
                to_uom=self.product_uom_id.id,
            )
        else:
            theoretical_qty = 0
        # Sanity check on the lot.
        if self.prod_lot_id:
            if self.product_id.tracking == 'none' or self.product_id != self.prod_lot_id.product_id:
                self.prod_lot_id = False

        if self.prod_lot_id and self.product_id.tracking == 'serial':
            # We force `product_qty` to 1 for SN tracked product because it's
            # the only relevant value aside 0 for this kind of product.
            self.product_qty = 1
        elif self.product_id and float_compare(self.product_qty, self.theoretical_qty,
                                               precision_rounding=self.product_uom_id.rounding) == 0:
            # We update `product_qty` only if it equals to `theoretical_qty` to
            # avoid to reset quantity when user manually set it.
            self.product_qty = theoretical_qty
        self.theoretical_qty = theoretical_qty

    @api.model_create_multi
    def create(self, vals_list):
        products = self.env['product.product'].browse([vals.get('product_id') for vals in vals_list])
        for product, values in zip(products, vals_list):
            if 'theoretical_qty' not in values:
                theoretical_qty = self.env['product.product'].get_theoretical_quantity(
                    values['product_id'],
                    values['location_id'],
                    lot_id=values.get('prod_lot_id'),
                    package_id=values.get('package_id'),
                    owner_id=values.get('partner_id'),
                    to_uom=values.get('product_uom_id'),
                )
                values['theoretical_qty'] = theoretical_qty
            if 'product_id' in values and 'product_uom_id' not in values:
                values['product_uom_id'] = product.product_tmpl_id.uom_id.id
        res = super(InstructionOrderLine, self).create(vals_list)
        return res

    def _get_virtual_location(self):
        virtual_location = self.env['stock.location'].search(
            [('id', 'child_of', self.organization_id.warehouse_id.view_location_id.id), ('scrap_location', '=', True)])
        if virtual_location:
            return virtual_location
        else:
            raise UserError('在庫ロスロケーションは未設定です。ご確認ください。')

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        self.ensure_one()
        return {
            'name': _('INV:') + (self.order_id.name or ''),
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': qty,
            'date': self.order_id.date,
            'x_organization_id': self.order_id.organization_id.id,
            'instruction_order_id': self.order_id.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': self.product_cost,
            'state': 'confirmed',
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'lot_id': self.prod_lot_id.id,
                'product_uom_qty': 0,  # bypass reservation here
                'product_uom_id': self.product_uom_id.id,
                'qty_done': qty,
                'package_id': out and self.package_id.id or False,
                'result_package_id': (not out) and self.package_id.id or False,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
            })]
        }

    def _get_account_id(self):
        if self.difference_qty > 0:
            account_id = self.env['ir.config_parameter'].sudo().get_param('ss_erp_stock_adjustment')
            if not account_id:
                raise UserError('棚卸差益勘定の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。（ss_erp_stock_adjustment）')
        else:
            account_id = self.env['ir.config_parameter'].sudo().get_param('ss_erp_stock_expense')
            if not account_id:
                raise UserError(
                    '棚卸減耗費勘定の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。（ss_erp_stock_expense）')
        return account_id

    def _generate_moves(self):
        vals_list = []
        for line in self:
            virtual_location = line._get_virtual_location()
            rounding = line.product_id.uom_id.rounding
            if float_is_zero(line.difference_qty, precision_rounding=rounding):
                continue
            if line.difference_qty > 0:  # found more than expected
                vals = line._get_move_values(line.difference_qty, virtual_location.id, line.location_id.id, False)
            else:
                vals = line._get_move_values(abs(line.difference_qty), line.location_id.id, virtual_location.id, True)
            vals_list.append(vals)
        return self.env['stock.move'].create(vals_list)

