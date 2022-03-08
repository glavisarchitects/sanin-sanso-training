# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


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
    type_id = fields.Many2one('product.template', related='order_id.type_id', string='棚卸種別')
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
        # res._check_no_duplicate_line()
        return res

    # def _check_no_duplicate_line(self):
    #     domain = [('product_id', 'in', self.product_id.ids), ('location_id', 'in', self.location_id.ids)]
    #     groupby_fields = ['product_id', 'location_id', 'partner_id', 'package_id', 'prod_lot_id', 'inventory_id']
    #     lines_count = {}
    #     for group in self.read_group(domain, ['product_id'], groupby_fields, lazy=False):
    #         key = tuple([group[field] and group[field][0] for field in groupby_fields])
    #         lines_count[key] = group['__count']
    #     for line in self:
    #         key = (line.product_id.id, line.location_id.id, line.partner_id.id, line.package_id.id, line.prod_lot_id.id,
    #                line.inventory_id.id)
    #         if lines_count[key] > 1:
    #             raise UserError(_("There is already one Instruction detail for this product,"
    #                               " you should rather modify this one instead of creating a new one."))
