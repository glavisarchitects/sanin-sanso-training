from odoo import fields, models, api
from datetime import datetime


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

    template_id = fields.Many2one(
        comodel_name='construction.template',
        string='工事テンプレート',
        required=False
    )

    picking_ids = fields.One2many('stock.picking', 'x_construction_order_id', string='配送')

    delivery_count = fields.Integer(string='工事出荷', compute='_compute_picking_ids')

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for rec in self:
            rec.delivery_count = len(rec.picking_ids)

    def action_view_delivery(self):
        '''
        This function returns an action that display existing delivery orders
        of given construction order. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")

        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        # Prepare the context.
        action['context'] = dict(self._context, default_partner_id=self.partner_id.id,
                                 default_picking_type_id=self.picking_type_id.id,
                                 default_origin=self.name,
                                 default_location_id=self.location_id.id,
                                 default_location_dest_id=self.location_dest_id.id,
                                 default_organization_id=self.organization_id.id,
                                 default_responsible_dept_id=self.organization_id.id
                                 )
        return action

    def _prepare_construction_component_data(self):
        template = self.template_id
        component_lines = [(5, 0, 0)]

        data = {}
        for component in template.component_line_ids:
            key = str(component.product_id.id) + '_' + str(component.product_uom_id.id)
            if key not in data.keys():
                data[key] = {
                    'product_uom_qty': component.product_uom_qty,
                    'product_id': component.product_id.id,
                    'product_uom_id': component.product_uom_id.id,
                }
            else:
                data[key]['product_uom_qty'] += component.product_uom_qty

        for v in data.values():
            component_lines.append((0, 0, v))

        return component_lines

    def _prepare_workoder_line(self):
        template = self.template_id

        self.construction_workorder_ids = False

        for workcenter_line in template.workcenter_line_ids:

            # 構成品を準備
            components = [(5, 0, 0)]
            for line in workcenter_line.workcenter_id.component_ids:
                components.append((0, 0, {
                    'product_uom_qty': line.product_uom_qty,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                }))

            workorder_lines = self.env['ss.erp.construction.workorder'].create({
                'construction_id': self.id,
                'name': workcenter_line.workcenter_id.name,
            })
            workorder_lines.workorder_component_ids = components

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if not self.template_id:
            self.construction_component_ids = False
            self.construction_workorder_ids = False
            return

        self.construction_component_ids = self._prepare_construction_component_data()

        self._prepare_workoder_line()

    @api.depends('construction_component_ids.product_uom_qty', 'construction_component_ids.sale_price',
                 'construction_component_ids.tax_id', 'construction_component_ids.standard_price')
    def _compute_amount(self):
        for rec in self:
            amount_purchased = 0
            amount_untaxed = 0
            amount_tax = 0

            for line in rec.construction_component_ids:
                amount_untaxed += line.product_uom_qty * line.sale_price
                amount_purchased += line.product_uom_qty * line.standard_price
                amount_tax += (line.product_uom_qty * line.sale_price) * line.tax_id.amount / 100

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

    def _prepare_stock_picking(self):
        for workorder in self.construction_workorder_ids:
            picking = {
                'partner_id': workorder.partner_id.id,
                'x_organization_id': workorder.organization_id.id,
                'x_responsible_dept_id': workorder.responsible_dept_id.id,
                'picking_type_id': workorder.picking_type_id.id,
                'location_id': workorder.location_id.id,
                'location_dest_id': workorder.location_dest_id.id,
                'scheduled_date': workorder.date_planned_start,
                'x_construction_order_id': self.id,
                'x_workorder_id': workorder.id
            }
            move_live = []
            for component in workorder.workorder_component_ids:
                if component.product_id.type == 'product':
                    move_live.append((0, 0, {
                        'name': component.product_id.name or '/',
                        'product_id': component.product_id.id,
                        'product_uom': component.product_uom_id.id,
                        'product_uom_qty': component.product_uom_qty,
                        'location_id': workorder.location_id.id,
                        'location_dest_id': workorder.location_dest_id.id,
                        'date': workorder.date_planned_start or datetime.now(),
                        'picking_type_id': workorder.picking_type_id.id,
                    }))

            picking['move_ids_without_package'] = move_live
            construction_picking = self.env['stock.picking'].create(picking)
            construction_picking.action_assign()

    def write(self, values):
        res = super(Construction, self).write(values)
        return res

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
                                                 inverse_name='construction_id', string='構成品',
                                                 tracking=True)
    construction_workorder_ids = fields.One2many(comodel_name='ss.erp.construction.workorder', ondelete="cascade",
                                                 inverse_name='construction_id', string='作業オーダー',
                                                 tracking=True)
    state = fields.Selection(
        string='ステータス',
        selection=[('draft', 'ドラフト'),
                   ('request_approve', '申請中'),
                   ('confirmed', '確認済'),
                   ('sent', '提出済'),
                   ('pending', '保留'),
                   ('order_received', '受注'),
                   ('progress', '進行中'),
                   ('done', '完了'),
                   ('lost', '失注'),
                   ('cancel', '取消')
                   ],
        default='draft',
        required=False, )

    def action_pending(self):
        self.write({'state': 'pending'})

    def action_receive_order(self):
        self._prepare_stock_picking()
        self.write({'state': 'order_received'})

    def action_mark_lost(self):
        self.write({'state': 'lost'})

    def action_sent(self):
        self.write({'state': 'sent'})

    def action_back_to_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_start(self):
        self.write({'state': 'progress'})

    def action_purchase(self):
        self.picking_ids.filtered(lambda r: r.picking_type_id.code == 'outgoing')
        return
