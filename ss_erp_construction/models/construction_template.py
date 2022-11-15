from odoo import fields, models, api


class ConstructionTemplate(models.Model):
    _name = 'construction.template'
    _description = '工事テンプレート'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    name = fields.Char(string='テンプレート名', copy=True)
    state = fields.Selection(
        string='ステータス',
        selection=[('new', '未申請'),
                   ('pending', '申請済み'),
                   ('approved', '承認済み'),
                   ('refused', '却下済み'),
                   ('cancel', '取消'),
                   ],default='new',
        required=False )
    code = fields.Char(string='コード', copy=True)

    display_name = fields.Char(string='名称', compute='_compute_display_name', store=True)
    user_id = fields.Many2one(
        comodel_name='res.users', default=lambda self: self.env.uid)

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '【%s】 %s' % (rec.code, rec.name)

    component_line_ids = fields.One2many(
        comodel_name='construction.template.component',
        inverse_name='template_id',
        string='工事構成品',
        compute='_compute_component_line_ids',
        required=False,
        ondelete='cascade',
        store=True,
        copy = True
    )

    @api.depends('workcenter_line_ids.workcenter_id.component_ids')
    def _compute_component_line_ids(self):
        for rec in self:
            rec.component_line_ids = False
            component_arr = []
            # component_arr = [(5, 0, 0)]
            if rec.workcenter_line_ids:
                for line in rec.workcenter_line_ids:
                    if line.workcenter_id.component_ids:
                        for component in line.workcenter_id.component_ids:
                            data = {
                                'template_id': rec.id,
                                'product_id': component.product_id.id,
                                'product_uom_qty': component.product_uom_qty,
                                'product_uom_id': component.product_uom_id.id,
                                'workcenter_id': line.workcenter_id.id,
                            }
                            component_arr.append((0, 0, data))
            if component_arr:
                rec.component_line_ids = component_arr

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True, string="会社", copy=True)

    workcenter_line_ids = fields.Many2many(
        comodel_name='construction.template.workcenter',
        string='工事構成品',
        required=False,
        store=True, copy=True
    )


class ConstructionTemplateComponent(models.Model):
    _name = 'construction.template.component'
    _description = '工事テンプレートの構成品'

    template_id = fields.Many2one(
        comodel_name='construction.template',
        string='工事テンプレート',
        ondelete='cascade',
        required=False)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='プロダクト',
        required=False)
    product_uom_qty = fields.Float(string='数量')
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True, string="単位カテゴリ")
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='単位',
        domain="[('category_id', '=', product_uom_category_id)]",
        required=False)
    workcenter_id = fields.Many2one('construction.workcenter', '作業区に消費')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True, string="会社")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id


class ConstructionTemplateWorkcenter(models.Model):
    _name = 'construction.template.workcenter'
    _description = '工事テンプレートの工程'

    workcenter_id = fields.Many2one('construction.workcenter', string='工程')
    spend_time = fields.Float('デフォルト所要時間', related='workcenter_id.spend_time')
    costs_hour = fields.Float(string='時間毎の費用', related='workcenter_id.costs_hour')
    currency_id = fields.Many2one(related='workcenter_id.currency_id')
