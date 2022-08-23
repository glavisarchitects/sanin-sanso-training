from odoo import fields, models, api


class Construction(models.Model):
    _name = 'ss.erp.construction'
    _description = '工事'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='シーケンス', default='新規')
    construction_name = fields.Char(string='工事名')
    sequence = fields.Char(string='シーケンス')
    organization_id = fields.Many2one(
        comodel_name='ss_erp.organization',
        string='組織',
        default=lambda self: self._get_default_x_organization_id(),
        required=False)
    responsible_dept_id = fields.Many2one(
        comodel_name='ss_erp.responsible.department',
        string='管轄部門',
        default=lambda self: self._get_default_x_responsible_dept_id()
    )

    company_id = fields.Many2one('res.company', string='会社', default=lambda self: self.env.user.company_id.id)

    currency_id = fields.Many2one('res.currency', '通貨', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)

    partner_id = fields.Many2one('res.partner', string='顧客', domain=[('x_is_customer', '=', True)], )

    picking_type_id = fields.Many2one('stock.picking.type', related='organization_id.warehouse_id.out_type_id',
                                      store=True, string='オペレーションタイプ')
    location_id = fields.Many2one('stock.location', related='organization_id.warehouse_id.lot_stock_id', store=True,
                                  string='構成品ロケーション')
    location_dest_id = fields.Many2one('stock.location', related='partner_id.property_stock_customer', store=True,
                                       string='配送ロケーション')

    amount_untaxed = fields.Monetary(string='税抜金額', compute='_compute_amount')
    amount_tax = fields.Monetary(string='税', compute='_compute_amount')
    amount_total = fields.Monetary(string='合計', compute='_compute_amount')
    margin = fields.Monetary(string='粗利益', compute='_compute_amount')
    margin_percent = fields.Float(string='マージン(%)')

    @api.depends('construction_component_ids.quantity', 'construction_component_ids.sale_price',
                 'construction_component_ids.tax_id', 'construction_component_ids.standard_price')
    def _compute_amount(self):
        for rec in self:
            amount_purchased = 0
            amount_untaxed = 0
            amount_tax = 0

            for line in rec.construction_component_ids:
                amount_untaxed += line.quantity * line.sale_price
                amount_purchased += line.quantity * line.standard_price
                amount_tax += (line.quantity * line.sale_price) * line.tax_id.amount / 100

            amount_total = amount_untaxed + amount_tax
            margin = amount_untaxed - amount_purchased
            margin_percent = margin / amount_untaxed if amount_untaxed != 0 else 100

            rec.amount_total = amount_total
            rec.amount_untaxed = amount_untaxed
            rec.margin = margin
            rec.margin_percent = margin_percent
            rec.amount_tax = amount_tax

    @api.model
    def create(self, values):
        # Auto create name sequence
        name = self.env['ir.sequence'].next_by_code('ss_erp.construction')
        values['name'] = name
        return super(Construction, self).create(values)

    def _get_default_x_organization_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id.organization_first
        else:
            return False

    def _get_default_x_responsible_dept_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id and employee_id.department_jurisdiction_first:
            return employee_id.department_jurisdiction_first[0]
        else:
            return False

    plan_date = fields.Date(string='予定日')
    user_id = fields.Many2one(comodel_name='res.users', string='担当者', default=lambda self: self.env.user)
    all_margin_rate = fields.Float(string='一律マージン率')
    construction_component_ids = fields.One2many(comodel_name='ss.erp.construction.component',
                                                 inverse_name='construction_id', string='構成品')
    construction_workorder_ids = fields.One2many(comodel_name='ss.erp.construction.workorder',
                                                 inverse_name='construction_id', string='作業オーダー')
    state = fields.Selection(
        string='ステータス',
        selection=[('draft', 'ドラフト'),
                   ('confirmed', '確認済'),
                   ('pending', '保留'),
                   ('order_received', '受注'),
                   ('progress', '進行中'),
                   ('done', '完了'),
                   ('lost', '失注')],
        required=False, )

    def action_pending(self):
        self.write({'state': 'pending'})

    def action_receive_order(self):
        self.write({'state': 'order_received'})

    def action_mark_lost(self):
        self.write({'state': 'lost'})

    # @api.onchange('all_margin_rate')
    # def _onchange_all_margin_rate(self):
    #     for rec in self.construction_component_ids:
    #         rec.margin_rate = self.all_margin_rate
    #         rec.sale_price = rec.standard_price * (1 + rec.margin_rate)
    #         rec.margin = (rec.sale_price - rec.standard_price) * rec.quantity


class ConstructionComponent(models.Model):
    _name = 'ss.erp.construction.component'
    _description = '構成品'

    product_id = fields.Many2one(comodel_name='product.product', string='プロダクト')
    quantity = fields.Float(string='数量')
    uom_id = fields.Many2one(comodel_name='uom.uom', string='単位')
    partner_id = fields.Many2one(comodel_name='res.partner', domain=[('x_is_vendor', '=', True)], string='仕入先')
    payment_term_id = fields.Many2one(comodel_name='account.payment.term', string='支払条件')
    standard_price = fields.Monetary(string='仕入価格')
    currency_id = fields.Many2one('res.currency', '通貨', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    tax_id = fields.Many2one(comodel_name='account.tax', string='税')
    sale_price = fields.Monetary(string='販売価格')
    margin = fields.Monetary(string='粗利益', compute='_compute_margin', store=True)
    margin_rate = fields.Float(string='マージン(%)', compute='_compute_margin', store=True)
    subtotal_exclude_tax = fields.Monetary(string='小計（税別）', compute='_compute_margin', store=True)
    subtotal = fields.Monetary(string='小計', compute='_compute_margin', store=True)
    construction_id = fields.Many2one(comodel_name='ss.erp.construction', string='工事')

    @api.depends('sale_price', 'construction_id.all_margin_rate')
    def _compute_margin(self):
        for rec in self:
            if rec.construction_id.all_margin_rate != 0:
                rec.margin_rate = rec.construction_id.all_margin_rate
                rec.sale_price = rec.standard_price * (1 + rec.margin_rate)
                rec.margin = (rec.sale_price - rec.standard_price) * rec.quantity
            else:
                rec.margin_rate = rec.sale_price / rec.standard_price - 1 if rec.standard_price != 0 else 1
                rec.margin = (rec.sale_price - rec.standard_price) * rec.quantity
            rec.subtotal_exclude_tax = rec.quantity * rec.sale_price
            rec.subtotal = rec.subtotal_exclude_tax * (1 + rec.tax_id.amount / 100)


class ConstructionWorkorder(models.Model):
    _name = 'ss.erp.construction.workorder'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '工事の作業オーダー'

    name = fields.Char(string='工程')
    organization_id = fields.Many2one(
        comodel_name='ss_erp.organization',
        string='組織',
        related='construction_id.organization_id',
        required=False)
    responsible_dept_id = fields.Many2one(
        comodel_name='ss_erp.responsible.department',
        string='管轄部門',
        related='construction_id.responsible_dept_id',
    )

    picking_type_id = fields.Many2one('stock.picking.type', related='construction_id.picking_type_id',
                                      store=True, string='オペレーションタイプ')
    location_id = fields.Many2one('stock.location', related='construction_id.location_id', store=True,
                                  string='構成品ロケーション')
    location_dest_id = fields.Many2one('stock.location', related='construction_id.location_dest_id', store=True,
                                       string='配送ロケーション')

    planned_labor_costs = fields.Monetary(string='[予定] 労務費')
    result_labor_costs = fields.Monetary(string='[実績] 労務費')
    planned_expenses = fields.Monetary(string='[予定] 経費')
    result_expenses = fields.Monetary(string='[実績] 経費')
    construction_work_notes = fields.Text(string='備考')
    total_amount = fields.Monetary(string='合計金額')
    date_planned_start = fields.Datetime(string='計画開始日')
    date_planned_finished = fields.Datetime(string='計画終了日')
    date_start = fields.Datetime(string='開始日')
    date_end = fields.Datetime(string='終了日')
    duration_expected = fields.Float(string='予想所要時間')
    duration = fields.Float(string='実所要時間')
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    state = fields.Selection([
        ('pending', '他の作業オーダー待ち'),
        ('ready', '準備完了'),
        ('progress', '進行中'),
        ('done', '完了'),
        ('cancel', '取消済み'),
    ], string='ステータス')
    construction_id = fields.Many2one(comodel_name='ss.erp.construction', string='工事')

    move_raw_ids = fields.One2many(comodel_name='stock.move', inverse_name='construction_workorder_id')
