from odoo import fields, models, api


class ConstructionTemplate(models.Model):
    _name = 'construction.template'
    _description = '工事テンプレート'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    name = fields.Char(string='テンプレート名')
    state = fields.Selection(
        string='ステータス',
        selection=[('new', '未申請'),
                   ('pending', '申請済み'),
                   ('approved', '承認済み'),
                   ('refused', '却下済み'),
                   ('cancel', '取消'),
                   ],
        required=False, )
    code = fields.Char(string='コード')

    display_name = fields.Char(string='名称', compute='_compute_display_name', store=True)

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '【%s】 %s' % (rec.code, rec.name)

    component_line_ids = fields.One2many(
        comodel_name='construction.template.line',
        inverse_name='template_id',
        string='工事構成品',
        compute='_compute_component_line_ids',
        required=False,
        store=True
    )

    @api.depends('operation_line_ids.component_ids')
    def _compute_component_line_ids(self):
        component_arr = [(5, 0, 0)]
        for operation_line in self.operation_line_ids:
            for component in operation_line.component_ids:
                data = {
                    'template_id': self.id,
                    'product_id': component.product_id.id,
                    'product_uom_qty': component.product_uom_qty,
                    'product_uom_id': component.product_uom_id.id,
                    'operation_id': operation_line.id
                }
                component_arr.append((0, 0, data))

        self.component_line_ids = component_arr

    operation_line_ids = fields.One2many(
        comodel_name='construction.template.operation',
        inverse_name='template_id',
        string='オペレーション',
        required=False)

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True, string="会社")


class ConstructionTemplateLine(models.Model):
    _name = 'construction.template.line'
    _description = '工事テンプレート明細'

    template_id = fields.Many2one(
        comodel_name='construction.template',
        string='工事テンプレート',
        required=False)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='プロダクト',
        required=False)
    product_uom_qty = fields.Float(string='数量')
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='単位',
        domain="[('category_id', '=', product_uom_category_id)]",
        required=False)
    operation_id = fields.Many2one(comodel_name='construction.template.operation')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True, string="会社")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id


class ConstructionTemplateOperation(models.Model):
    _name = 'construction.template.operation'
    _description = '工事テンプレートオペレーション'

    name = fields.Char(
        string='工程',
        required=False)
    workcenter_id = fields.Many2one(
        comodel_name='construction.workcenter',
        string='作業区',
        required=False)

    time_cycle = fields.Float(
        string='デフォルト所要時間',
        required=False)

    template_id = fields.Many2one(
        comodel_name='construction.template',
        string='工事テンプレート',
        required=False)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True, string="会社")
    component_ids = fields.One2many(
        comodel_name='construction.template.operation.component',
        inverse_name='operation_id',
        string='構成品',
        required=False)


class ConstructionTemplateOperationComponent(models.Model):
    _name = 'construction.template.operation.component'
    _description = '工事テンプレートオペレーションの構成品'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='プロダクト',
        required=False)
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='単位',
        domain="[('category_id', '=', product_uom_category_id)]",
        required=False)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    product_uom_qty = fields.Float(string='消費量')
    operation_id = fields.Many2one(
        comodel_name='construction.template.operation',
        string='オペレーション',
        required=False)
