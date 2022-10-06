from odoo import fields, models, api


class ConstructionWorkcenter(models.Model):
    _name = 'construction.workcenter'
    _description = '工事作業区'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code desc'

    name = fields.Char('作業区名')
    code = fields.Char('コード')
    spend_time = fields.Float('デフォルト所要時間')
    costs_hour = fields.Float(string='時間毎の費用')
    currency_id = fields.Many2one('res.currency', '通貨', default=lambda self: self.company_id.currency_id.id)
    note = fields.Text('説明')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True, string="会社")
    active = fields.Boolean(default=True)
    component_ids = fields.One2many('construction.workcenter.component', 'workcenter_id')
    template_id = fields.Many2one('construction.template')
    user_id = fields.Many2one(
        comodel_name='res.users', default=lambda self: self.env.uid)


class ConstructionWorkcenterComponent(models.Model):
    _name = 'construction.workcenter.component'
    _description = '工事作業区の構成品'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='プロダクト',
        required=False)
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='単位',
        domain="[('category_id', '=', product_uom_category_id)]",
        required=False)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True, string='単位カテゴリ')
    product_uom_qty = fields.Float(string='消費量')
    workcenter_id = fields.Many2one(
        comodel_name='construction.workcenter',
        string='作業区',
        required=False)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id