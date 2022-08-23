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
    code = fields.Char(string='参照')

    display_name = fields.Char(string='名称', compute='_compute_display_name', store=True)

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '[%s] %s' % (rec.code, rec.name)

    template_line_ids = fields.One2many(
        comodel_name='construction.template.line',
        inverse_name='template_id',
        string='工事構成品',
        required=False)
    operation_line_ids = fields.One2many(
        comodel_name='construction.template.operation',
        inverse_name='template_id',
        string='オペレーション',
        required=False)

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)


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
    product_qty = fields.Float(string='数量')
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='単位',
        required=False)
    operation_id = fields.Many2one(comodel_name='construction.template.operation')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)


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
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
