from odoo import fields, models, api


class ConstructionComponent(models.Model):
    _name = 'ss.erp.construction.component'
    _description = '構成品'

    product_id = fields.Many2one(comodel_name='product.product', string='プロダクト', tracking=True)
    product_uom_qty = fields.Float(string='数量', tracking=True)
    qty_reserved = fields.Float(string='引当済み', compute='_compute_quantity', store=True)
    qty_done = fields.Float(string='消費済み', compute='_compute_quantity', store=True)
    product_uom_id = fields.Many2one(comodel_name='uom.uom', string='単位', tracking=True,
                                     domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True, string='単位カテゴリ')
    partner_id = fields.Many2one(comodel_name='res.partner', domain=[('x_is_vendor', '=', True)], string='仕入先',
                                 tracking=True)
    payment_term_id = fields.Many2one(comodel_name='account.payment.term', string='支払条件', tracking=True)
    standard_price = fields.Monetary(string='仕入価格', tracking=True)
    currency_id = fields.Many2one('res.currency', '通貨', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    tax_id = fields.Many2one(comodel_name='account.tax', string='税', tracking=True)
    sale_price = fields.Monetary(string='販売価格', tracking=True)
    margin = fields.Monetary(string='粗利益', compute='_compute_margin', store=True)
    margin_rate = fields.Float(string='マージン(%)', compute='_compute_margin', store=True)
    subtotal_exclude_tax = fields.Monetary(string='小計（税別）', compute='_compute_margin', store=True)
    subtotal = fields.Monetary(string='小計', compute='_compute_margin', store=True)
    construction_id = fields.Many2one(comodel_name='ss.erp.construction', string='工事')

    @api.depends('construction_id.move_ids', 'construction_id.move_ids.reserved_availability',
                 'construction_id.move_ids.quantity_done')
    def _compute_quantity(self):
        for line in self:
            product_move_ids = line.construction_id.move_ids.filtered(
                lambda x: x.product_id.id == line.product_id.id and x.product_uom.id == line.product_uom_id.id)
            line.qty_reserved = sum([m.reserved_availability for m in product_move_ids])
            line.qty_done = sum([m.quantity_done for m in product_move_ids])

    @api.depends('sale_price', 'construction_id.all_margin_rate', 'tax_id')
    def _compute_margin(self):
        for rec in self:
            if rec.construction_id.all_margin_rate != 0:
                rec.margin_rate = rec.construction_id.all_margin_rate
                rec.sale_price = rec.standard_price * (1 + rec.margin_rate)
                rec.margin = (rec.sale_price - rec.standard_price) * rec.product_uom_qty
            else:
                rec.margin_rate = rec.sale_price / rec.standard_price - 1 if rec.standard_price != 0 else 1
                rec.margin = (rec.sale_price - rec.standard_price) * rec.product_uom_qty
            rec.subtotal_exclude_tax = rec.product_uom_qty * rec.sale_price
            rec.subtotal = rec.subtotal_exclude_tax * (1 + rec.tax_id.amount / 100)

