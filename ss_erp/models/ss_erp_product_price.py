from odoo import models, api, fields, _
import time
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.fields import Datetime, Date


class ProductPrice(models.Model):
    _name = 'ss_erp.product.price'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Product Price'

    name = fields.Char('価格リスト名')
    company_id = fields.Many2one('res.company', '会社', copy=False)
    organization_id = fields.Many2one('ss_erp.organization', '組織', copy=False)
    pricelist_class = fields.Many2one('product.pricelist.class', '価格リスト区分', copy=False)
    # pricelist_id = fields.Many2one('product.pricelist', '価格リスト')
    partner_id = fields.Many2one('res.partner', '取引先', copy=False)
    product_id = fields.Many2one('product.product', 'プロダクト', copy=False)
    uom_id = fields.Many2one('uom.uom', '単位', copy=False)
    product_uom_qty_min = fields.Float('数量範囲(最小値)')
    product_uom_qty_max = fields.Float('数量範囲(最大値)')
    price_unit = fields.Float('単価')
    start_date = fields.Date('有効開始日')
    end_date = fields.Date('有効終了日', default=fields.Date.from_string('2099-12-31'))
    description = fields.Text('内部注記')

    has_organization = fields.Selection(store=True, related='pricelist_class.organization_id')
    has_partner = fields.Selection(store=True, related='pricelist_class.partner_id')
    has_uom = fields.Selection(store=True, related='pricelist_class.uom_id')
    has_product_uom_qty_min = fields.Selection(store=True, related='pricelist_class.product_uom_qty_min')
    has_product_uom_qty_max = fields.Selection(store=True, related='pricelist_class.product_uom_qty_max')
    active = fields.Boolean(default=True)
    #
    @api.onchange('end_date')
    def _check_end_date(self):
        current_date = fields.Date.today()
        if self.end_date:
            if self.end_date < current_date:
                raise ValidationError(_("有効終了日が過去日付のため登録できません"))

    @api.onchange('start_date', 'end_date')
    def _onchange_end_date(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError(_("有効終了日は、開始日より過去の日付は選択できません"))

    #
    @api.constrains('product_uom_qty_min', 'product_uom_qty_max')
    def _check_raise_price_min_max(self):
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
        new_start_date = (False if vals.get('start_date') is None else fields.Date.from_string(vals['start_date'])) or self.start_date
        new_end_date = (False if vals.get('end_date') is None else fields.Date.from_string(vals['end_date'])) or self.end_date
        # pricelist_class = 'pricelist_class' in vals or self.company_id.id
        # organization = 'pricelist_class' in vals or self.company_id.id

        val_check = [
                ('company_id', '=', new_company_id),
                ('pricelist_class', '=', new_pricelist_class),
                ('product_id', '=', new_product_id),
                ('uom_id', '=', new_uom_id),
                ('product_uom_qty_min', '=', new_product_uom_qty_min),
                ('product_uom_qty_max', '=', new_product_uom_qty_max),

            ]
        if new_partner_id:
            val_check.append(('partner_id', '=', new_partner_id))
        if new_organization_id:
            val_check.append(('organization_id', '=', new_organization_id))

        product_pricelist_duplicate = self.env['ss_erp.product.price'].search(val_check)
        if product_pricelist_duplicate and product_pricelist_duplicate != self:
            for exist in product_pricelist_duplicate:
                # if exist != self and ((exist.end_date > new_start_date and exist.start_date < new_end_date) or
                #                       (exist.start_date < new_end_date and exist.end_date < new_end_date) or
                #                       (exist.start_date < new_start_date and exist.end_date < new_end_date)):
                if (exist.start_date <= new_start_date <= exist.end_date) or (exist.start_date <= new_end_date <= exist.end_date):
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
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Product Price List Class'

    name = fields.Char('名称')
    description = fields.Char('説明')
    organization_id = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], '組織', default='optional')
    partner_id = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], '取引先', default='optional')
    uom_id = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], '単位', default='optional')
    product_uom_qty_min = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], '数量範囲(最小値)', default='optional')
    product_uom_qty_max = fields.Selection([('required', '必須'), ('optional', 'オプション'), ('no', 'なし')], '数量範囲(最大値)', default='optional')
