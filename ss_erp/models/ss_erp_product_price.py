from odoo import models, api, fields, _
import time
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date


class ProductPrice(models.Model):
    _name = 'ss_erp.product.price'
    _description = 'Product Price'

    name = fields.Char('名称', copy=False)
    company_id = fields.Many2one('res.company', '会社')
    organization_id = fields.Many2one('ss_erp.organization', '組織')
    pricelist_class = fields.Many2one('product.pricelist.class', '価格リスト区分')
    pricelist_id = fields.Many2one('product.pricelist', '価格リスト')
    partner_id = fields.Many2one('res.partner', '取引先')
    product_id = fields.Many2one('product.product', 'プロダクト')
    uom_id = fields.Many2one('uom.uom', '単位')
    product_uom_qty_min = fields.Float('数量範囲(最小値)')
    product_uom_qty_max = fields.Float('数量範囲(最大値)')
    price_unit = fields.Float('単価')
    start_date = fields.Date('有効開始日')
    end_date = fields.Date('有効終了日', default=time.strftime('2099-12-31'))
    description = fields.Text('内部注記')

    has_organization = fields.Selection(store=True, related='pricelist_class.organization_id')
    has_partner = fields.Selection(store=True, related='pricelist_class.partner_id')
    has_uom = fields.Selection(store=True, related='pricelist_class.uom_id')
    has_product_uom_qty_min = fields.Selection(store=True, related='pricelist_class.product_uom_qty_min')
    has_product_uom_qty_max = fields.Selection(store=True, related='pricelist_class.product_uom_qty_max')

    _sql_constraints = [
        ('_unique', 'unique (name)', "Two pricelist cannot have the same name."),
    ]

    #
    @api.onchange('start_date', 'end_date')
    def _onchange_start_end_date(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError(_("有効終了日は、開始日より過去の日付は選択できません"))

    #
    @api.onchange('product_uom_qty_min', 'product_uom_qty_max')
    def _onchange_raise_price_min_max(self):
        if self.price_unit:
            if self.product_uom_qty_min > self.product_uom_qty_max:
                raise ValidationError(_("数量範囲(最大値)以下を入力して下さい。"))

    # Check condition prevent duplicate pricelist
    def _check_duplicate_pricelist(self, vals):
        new_company_id = (False if vals.get('company_id') is None else vals['company_id']) or self.company_id.id
        new_pricelist_class = (False if vals.get('pricelist_class') is None else vals['pricelist_class']) or self.pricelist_class.id
        new_organization_id = (False if vals.get('organization_id') is None else vals['organization_id']) or self.organization_id.id
        new_partner_id = (False if vals.get('partner_id') is None else vals['partner_id']) or self.partner_id.id
        new_product_id = (False if vals.get('product_id') is None else vals['product_id']) or self.product_id.id
        new_uom_id = (False if vals.get('uom_id') is None else vals['uom_id']) or self.uom_id.id
        new_product_uom_qty_min = (False if vals.get('product_uom_qty_min') is None else vals['product_uom_qty_min']) or self.product_uom_qty_min
        new_product_uom_qty_max = (False if vals.get('product_uom_qty_max') is None else vals['product_uom_qty_max']) or self.product_uom_qty_max
        new_start_date = datetime.strptime((False if vals.get('start_date') is None else vals['start_date']) or self.start_date, '%Y-%m-%d')
        new_end_date = datetime.strptime((False if vals.get('end_date') is None else vals['end_date']) or self.end_date , '%Y-%m-%d')
        # pricelist_class = 'pricelist_class' in vals or self.company_id.id
        # organization = 'pricelist_class' in vals or self.company_id.id
        if new_company_id and new_pricelist_class and new_organization_id and new_partner_id and\
                new_product_id and new_uom_id and new_start_date and new_end_date:

            product_pricelist_duplicate = self.env['ss_erp.product.price'].search([
                ('company_id', '=', new_company_id),
                ('pricelist_class', '=', new_pricelist_class),
                ('organization_id', '=', new_organization_id),
                ('partner_id', '=', new_partner_id),
                ('product_id', '=', new_product_id),
                ('uom_id', '=', new_uom_id),
                ('product_uom_qty_min', '=', new_product_uom_qty_min),
                ('product_uom_qty_max', '=', new_product_uom_qty_max),

            ])
            if len(product_pricelist_duplicate) > 0:
                for dup in product_pricelist_duplicate:
                    if dup.end_date > new_start_date or dup.start_date > new_end_date:
                        raise ValidationError(_('既に登録されている条件と期間が重なっているため登録できません'))

    @api.model
    def create(self, vals):
        self._check_duplicate_pricelist(vals)
        return super(ProductPrice, self).create(vals)

    def write(self, vals):
        self._check_duplicate_pricelist(vals)
        return super(ProductPrice, self).write(vals)


#
class ProductPriceClass(models.Model):
    _name = 'product.pricelist.class'
    _description = 'Product Price List Class'

    name = fields.Char('名称')
    description = fields.Char('説明')
    organization_id = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], '組織')
    partner_id = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], '取引先')
    uom_id = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], '単位')
    product_uom_qty_min = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], '数量範囲(最小値)')
    product_uom_qty_max = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], '数量範囲(最大値)')
