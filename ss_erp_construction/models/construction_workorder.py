from odoo import fields, models, api
from datetime import datetime


class ConstructionWorkorder(models.Model):
    _name = 'ss.erp.construction.workorder'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '工事の作業オーダー'

    name = fields.Char(string='工程')
    organization_id = fields.Many2one(
        comodel_name='ss_erp.organization',
        string='組織',
        related='construction_id.organization_id',
        store=True,
        required=False)
    responsible_dept_id = fields.Many2one(
        comodel_name='ss_erp.responsible.department',
        string='管轄部門',
        store=True,
        related='construction_id.responsible_dept_id',
    )

    workcenter_id = fields.Many2one(
        comodel_name='construction.workcenter',
        string='作業区',
        required=False)

    picking_type_id = fields.Many2one('stock.picking.type', related='construction_id.picking_type_id',
                                      store=True, string='オペレーションタイプ')
    location_id = fields.Many2one('stock.location', related='construction_id.location_id', store=True,
                                  string='構成品ロケーション')
    location_dest_id = fields.Many2one('stock.location', related='construction_id.location_dest_id', store=True,
                                       string='配送ロケーション')

    partner_id = fields.Many2one(related='construction_id.partner_id', store=True)

    planned_labor_costs = fields.Monetary(string='[予定] 労務費')
    result_labor_costs = fields.Monetary(string='[実績] 労務費')
    planned_expenses = fields.Monetary(string='[予定] 経費')
    result_expenses = fields.Monetary(string='[実績] 経費')
    construction_work_notes = fields.Text(string='備考')
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
    workorder_component_ids = fields.One2many(
        comodel_name='ss.erp.construction.workorder.component',
        inverse_name='workorder_id',
        string='構成品',
        required=False)

    def _prepare_stock_picking(self):
        picking = {
            'partner_id': self.partner_id.id,
            'x_organization_id': self.organization_id.id,
            'x_responsible_dept_id': self.responsible_dept_id.id,
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'scheduled_date': self.date_planned_start,
            'x_construction_order_id': self.id,
            'x_workorder_id': self.id
        }
        move_live = []
        for component in self.workorder_component_ids:
            if component.product_id.type == 'product':
                move_live.append((0, 0, {
                    'name': component.product_id.name or '/',
                    'product_id': component.product_id.id,
                    'product_uom': component.product_uom_id.id,
                    'product_uom_qty': component.product_uom_qty,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'date': self.date_planned_start or datetime.now(),
                    'picking_type_id': self.picking_type_id.id,
                }))

        picking['move_ids_without_package'] = move_live
        self.env['stock.picking'].create(picking).action_assign()


class ConstructionWorkorderComponent(models.Model):
    _name = 'ss.erp.construction.workorder.component'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '作業オーダーの構成品'

    workorder_id = fields.Many2one(
        comodel_name='ss.erp.construction.workorder',
        string='作業オーダー',
        required=False)

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='プロダクト',
        required=False)
    product_uom_qty = fields.Float(string='数量')
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True, string='単位カテゴリ')
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='単位',
        domain="[('category_id', '=', product_uom_category_id)]",
        required=False)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True, string="会社")


class ConstructionWorkorderTimesheet(models.Model):
    _name = 'ss.erp.construction.workorder.timesheet'
    _description = '作業オーダーのタイムシート'

    name = fields.Char()
