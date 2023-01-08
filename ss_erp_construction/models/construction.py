from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError, AccessError


class Construction(models.Model):
    _name = 'ss.erp.construction'
    _description = '工事'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(string='シーケンス', default='新規')
    construction_name = fields.Char(string='工事名', copy=True)
    # sequence = fields.Char(string='シーケンス')
    organization_id = fields.Many2one(
        comodel_name='ss_erp.organization',
        string='組織',
        default=lambda self: self._get_default_x_organization_id(),
        required=False, copy=True)
    responsible_dept_id = fields.Many2one(
        comodel_name='ss_erp.responsible.department',
        string='管轄部門', copy=True,
        default=lambda self: self._get_default_x_responsible_dept_id()
    )

    estimate_approval_status = fields.Selection([('new', '未申請'),
                                                 ('pending', '申請済'),
                                                 ('approved', '確認済'),
                                                 ('refused', '却下済'),
                                                 ('cancel', '取消')], string='承認ステータス', default='new')

    validate_approval_status = fields.Selection([('new', '未申請'),
                                                 ('pending', '申請済'),
                                                 ('approved', '確認済'),
                                                 ('refused', '却下済'),
                                                 ('cancel', '取消')], string='承認ステータス', default='new')

    invoice_status = fields.Selection([('invoiced', '完全請求書'),
                                       ('to_invoice', '請求対象'),
                                       ('no', '請求対象なし')
                                       ], string='請求書ステータス', compute='_compute_invoice_status', store=True)

    @api.depends('construction_component_ids.qty_to_invoice', 'state')
    def _compute_invoice_status(self):
        for rec in self:
            if rec.state not in ('order_received', 'progress', 'done'):
                rec.invoice_status = 'no'
            else:
                invoice_lst = rec.construction_component_ids.filtered(lambda x: x.qty_to_invoice != 0)
                if invoice_lst:
                    rec.invoice_status = 'to_invoice'
                else:
                    rec.invoice_status = 'invoiced'

    def _get_default_x_organization_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id.organization_first
        else:
            return False

    def _get_default_x_responsible_dept_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id and employee_id.department_jurisdiction_first:
            return employee_id.department_jurisdiction_first
        else:
            return False

    company_id = fields.Many2one('res.company', string='会社', default=lambda self: self.env.user.company_id.id,
                                 copy=True)

    currency_id = fields.Many2one('res.currency', '通貨', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id, copy=True)

    partner_id = fields.Many2one('res.partner', string='顧客', domain=[('x_is_customer', '=', True)], copy=True, )

    picking_type_id = fields.Many2one('stock.picking.type', store=True, string='オペレーションタイプ', copy=True)

    @api.onchange('organization_id')
    def _onchange_organization_id(self):
        self.picking_type_id = None
        if self.organization_id:
            return {'domain': {
                'picking_type_id': [('x_organization_id', '=', self.organization_id.id), ('code', '=', 'outgoing')]
            }}

    warehouse_id = fields.Many2one('stock.warehouse', related='organization_id.warehouse_id',
                                   store=True, string='倉庫', copy=True)
    location_id = fields.Many2one('stock.location', related='organization_id.warehouse_id.lot_stock_id', store=True,
                                  string='構成品ロケーション', copy=True)
    location_dest_id = fields.Many2one('stock.location', related='partner_id.property_stock_customer', store=True,
                                       string='配送ロケーション', copy=True)

    amount_untaxed = fields.Monetary(string='税抜金額', compute='_compute_amount', store=True)
    amount_tax = fields.Monetary(string='税', compute='_compute_amount', store=True)
    amount_total = fields.Monetary(string='合計', compute='_compute_amount', store=True)
    margin = fields.Monetary(string='粗利益', compute='_compute_amount', store=True)
    margin_percent = fields.Float(string='マージン(%)', store=True)

    template_id = fields.Many2one(
        comodel_name='construction.template',
        string='工事テンプレート',
        required=False, copy=True
    )

    picking_ids = fields.One2many('stock.picking', 'x_construction_order_id', string='配送')

    delivery_count = fields.Integer(string='工事出荷', compute='_compute_picking_ids')
    delivery_purchase_order_count = fields.Integer(string='購買', compute='_compute_purchase_order_count')

    client_order_ref = fields.Char(string='顧客参照', copy=False)

    invoice_count = fields.Integer(compute='_compute_invoice_count')

    category_id = fields.Many2one("ss_erp.construction.category", string="工事種別", copy=True)

    show_confirmation_button = fields.Boolean(compute='_compute_show_confirmation_button')

    # 注文請書 tab field
    # form_type = fields.Selection([('ss_to_orderer', 'SS→発注者'), ('coo_company_to_ss', '努力会社→SS')], default='ss_to_orderer', string='帳票タイプ')
    export_type = fields.Selection([('complete_set', '一式'), ('detail', '明細')], default='complete_set',
                                   string='出力タイプ')
    receipt_type = fields.Selection(
        string='入金手段',
        selection=[
            ('bank', '振込'),
            ('transfer', '振替'),
            ('bills', '手形'),
            ('cash', '現金'),
            ('paycheck', '小切手'),
            ('branch_receipt', '他店入金'),
            ('offset', '相殺'), ],
        required=False, )
    order_number = fields.Char(string='注文番号', compute='_compute_order_number')
    delivery_location = fields.Char(string='受渡場所')
    other_conditions = fields.Char(string='その他条件')

    @api.depends('name', 'plan_date')
    def _compute_order_number(self):
        for rec in self:
            if rec.name and rec.plan_date:
                rec.order_number = rec.plan_date.strftime("%Y%m%d") + '-' + rec.name.replace('工事', '')
            else:
                rec.order_number = ''

    @api.depends('amount_total')
    def _compute_show_confirmation_button(self):

        for rec in self:
            minium_value = self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_estimate_report')
            if not minium_value:
                raise UserError(
                    "承認金額の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(ss_erp_construction_estimate_report)")
            minium_value = float(minium_value)
            rec.show_confirmation_button = True if (
                    0 < rec.amount_total < minium_value or rec.estimate_approval_status == 'approved') else False

    def _compute_invoice_count(self):
        Invoice = self.env['account.move']
        can_read = Invoice.check_access_rights('read', raise_exception=False)
        for rec in self:
            rec.invoice_count = can_read and Invoice.search_count([('x_construction_order_id', '=', rec.id)]) or 0

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for rec in self:
            rec.delivery_count = len(rec.picking_ids)

    def _compute_purchase_order_count(self):
        for rec in self:
            rec.delivery_purchase_order_count = len(
                self.env['purchase.order'].search([('x_construction_order_id', '=', rec.id)]))

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
                    'standard_price': component.product_id.product_tmpl_id.standard_price,
                    'tax_id': component.product_id.product_tmpl_id.taxes_id[
                        0].id if component.product_id.product_tmpl_id.taxes_id else False,
                    'margin_rate': self.all_margin_rate,
                    'sale_price': component.product_id.product_tmpl_id.standard_price / (1 - self.all_margin_rate),
                    'name': component.product_id.name,
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
                'duration_expected': workcenter_line.spend_time,
                'costs_hour': workcenter_line.costs_hour
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

    # def _prepare_stock_picking(self):
    #     if self.construction_workorder_ids:
    #         for workorder in self.construction_workorder_ids:
    #             workorder._prepare_stock_picking()

    def write(self, values):
        res = super(Construction, self).write(values)
        return res

    plan_date = fields.Date(string='予定日', copy=True)
    date_planed_finished = fields.Date(string='終了予定日', copy=True)
    user_id = fields.Many2one(comodel_name='res.users', string='担当者', default=lambda self: self.env.user, copy=True)
    all_margin_rate = fields.Float(string='一律マージン率', copy=True)
    construction_component_ids = fields.One2many(comodel_name='ss.erp.construction.component',
                                                 inverse_name='construction_id', string='構成品',
                                                 tracking=True, copy=True)
    construction_workorder_ids = fields.One2many(comodel_name='ss.erp.construction.workorder', ondelete="cascade",
                                                 inverse_name='construction_id', string='作業オーダ',
                                                 tracking=True, copy=True)

    fiscal_position_id = fields.Many2one('account.fiscal.position', string='会計ポジション', copy=True)

    payment_term_id = fields.Many2one(comodel_name='account.payment.term', string='支払条件', tracking=True, copy=True)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id and self.partner_id.property_payment_term_id:
            self.payment_term_id = self.partner_id.property_payment_term_id.id
        else:
            self.payment_term_id = False

    state = fields.Selection(
        string='ステータス',
        selection=[('draft', 'ドラフト'),
                   ('request_approve', '申請中'),
                   ('confirmed', '確認済'),
                   ('pending', '保留'),
                   ('order_received', '受注'),
                   ('progress', '進行中'),
                   ('done', '完了'),
                   ('lost', '失注'),
                   ('cancel', '取消')
                   ],
        default='draft',
        required=False, )

    # Estimation Tab 2022/09/28
    print_type = fields.Selection(string='出力パターン',
                                  selection=[('set', '一式'),
                                             ('detail', '明細'),
                                             ], copy=True, )

    is_tax_exclude = fields.Selection(string='消費税',
                                      selection=[('included', '税込'),
                                                 ('exclude', '税抜'),
                                                 ], copy=True, )

    printed_user = fields.Many2one('res.users', string='作成者', copy=True)
    sequence_number = fields.Char(string='文書番号')
    output_date = fields.Date(string='出力日付', copy=True)
    expire_date = fields.Date(string='有効期限', copy=True)
    estimation_note = fields.Char(string='備考', copy=True)

    # 社内用
    is_in_house = fields.Boolean('社内用', default=False, copy=False)

    @api.onchange('all_margin_rate')
    def _onchange_all_margin_rate(self):
        if self.construction_component_ids:
            for line in self.construction_component_ids:
                line.margin_rate = self.all_margin_rate
                line.sale_price = line.standard_price / (1 - line.margin_rate)
                line.margin = (line.sale_price - line.standard_price) * line.product_uom_qty
                line.subtotal_exclude_tax = line.product_uom_qty * line.sale_price
                line.subtotal = line.subtotal_exclude_tax * (1 + line.tax_id.amount / 100)

    @api.onchange('is_tax_exclude')
    def _onchange_is_tax_exclude(self):
        if self.is_tax_exclude == 'exclude':
            remarks = self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_estimate_remarks')
            if remarks:
                self.estimation_note = remarks
        else:
            self.estimation_note = ''

    red_notice = fields.Text("注記欄")

    def action_pending(self):
        self.write({'state': 'pending'})

    def action_receive_order(self):
        self._prepare_stock_picking()
        self.write({'state': 'order_received'})

    # def action_print_estimation(self):
    #     print("estimation")

    def action_mark_lost(self):
        self.write({'state': 'lost'})

    def action_start(self):
        self.write({'state': 'progress'})

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_back_to_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_validate(self):
        self.write({'state': 'done'})

    def action_view_purchase_order(self):
        purchase_order_ids = self.env['purchase.order'].search([('x_construction_order_id', '=', self.id)]).ids
        action = self.env['ir.actions.act_window']._for_xml_id('purchase.purchase_rfq')
        action['domain'] = [('id', 'in', purchase_order_ids)]
        action['view_mode'] = 'tree'
        return action

    def action_purchase(self):
        if self.construction_component_ids:
            new_po = []
            for rec in self.construction_component_ids.filtered(lambda x: x.display_type == False):
                if rec.product_id.type != "consu" and self.partner_id:
                    po = rec._run_buy()
                    if po:
                        new_po.append(po.id)
            if new_po:
                action = self.env['ir.actions.act_window']._for_xml_id('purchase.purchase_rfq')
                action['domain'] = [('id', 'in', new_po)]
                action['view_mode'] = 'tree'
                return action
            else:
                raise UserError("購買対象のプロダクトがありません。")
        else:
            raise UserError("購買対象のプロダクトがありません。")

    def action_view_invoice(self):
        invoices = self.env['account.move'].search([('x_construction_order_id', '=', self.id)])
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_move_type': 'out_invoice',
        }
        action['context'] = context
        return action

    @api.model
    def _nothing_to_invoice_error(self):
        msg = _("""請求するものは何もありません！""")
        return UserError(msg)

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal = self.env['account.journal'].sudo().search([('type', '=', 'sale'), ('x_is_construction', '=', True)])
        if not journal:
            raise UserError('工事販売仕訳帳をご確認ください。')

        invoice_vals = {
            'ref': self.client_order_ref,
            'move_type': 'out_invoice',
            'invoice_origin': self.name,
            'x_organization_id': self.organization_id.id,
            'x_responsible_user_id': self.user_id.id,
            'x_responsible_dept_id': self.responsible_dept_id.id,
            'x_construction_order_id': self.id,
            'invoice_user_id': self.user_id.id,
            'partner_id': self.partner_id.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(
                self.partner_id.id)).id,
            'partner_shipping_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'journal_id': journal.id,
            'invoice_payment_term_id': self.payment_term_id.id,
            'partner_bank_id': self.partner_id.bank_ids[:1].id,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals

    def _get_invoiceable_lines(self):
        return self.construction_component_ids.filtered(lambda x: x.qty_to_invoice != 0 and not x.display_type)

    @api.model
    def _prepare_down_payment_section_line(self, **optional_values):
        """
        Prepare the dict of values to create a new down payment section for a construction order line.

        :param optional_values: any parameter that should be added to the returned down payment section
        """
        context = {'lang': self.partner_id.lang}
        down_payments_section_line = {
            'display_type': 'line_section',
            'name': _('前受金'),
            'product_id': False,
            'product_uom_id': False,
            'quantity': 0,
            'discount': 0,
            'price_unit': 0,
            'account_id': False
        }
        del context
        if optional_values:
            down_payments_section_line.update(optional_values)
        return down_payments_section_line

    def _create_invoices(self, final=False, date=None):
        """
        Create the invoice associated to the Construction Order.
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        invoice_vals_list = []
        invoice_item_sequence = 0  # Incremental sequencing to keep the lines order on the invoice.

        invoice_vals = self._prepare_invoice()
        invoiceable_lines = self._get_invoiceable_lines()

        if not self.construction_component_ids.filtered(lambda x: x.qty_to_invoice != 0):
            raise self._nothing_to_invoice_error()

        invoice_line_vals = []
        down_payment_section_added = False
        for line in invoiceable_lines:
            if not down_payment_section_added and line.is_downpayment:
                # Create a dedicated section for the down payments
                # (put at the end of the invoiceable_lines)
                invoice_line_vals.append(
                    (0, 0, self._prepare_down_payment_section_line(
                        sequence=invoice_item_sequence,
                    )),
                )
                down_payment_section_added = True
                invoice_item_sequence += 1
            if line.qty_to_invoice != 0:
                invoice_line_vals.append(
                    (0, 0, line._prepare_invoice_line(
                        sequence=invoice_item_sequence,
                    )),
                )
            invoice_item_sequence += 1

        invoice_vals['invoice_line_ids'] += invoice_line_vals
        invoice_vals_list.append(invoice_vals)

        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(
            invoice_vals_list)

        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        return moves

    # def write(self, vals):
    #     super().write(vals)
    #     if not self.construction_component_ids:
    #         raise UserError('構成品の明細を追加してください。')

    def _prepare_stock_picking(self):
        picking = {
            'partner_id': self.partner_id.id,
            'x_organization_id': self.organization_id.id,
            'x_responsible_dept_id': self.responsible_dept_id.id,
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'scheduled_date': self.plan_date,
            'x_construction_order_id': self.id,
        }
        move_live = []
        for component in self.construction_component_ids:
            if component.product_id.type == 'product' and component.qty_to_buy > 0 and component.qty_available > 0:
                move_live.append((0, 0, {
                    'name': component.product_id.name or '/',
                    'product_id': component.product_id.id,
                    'product_uom': component.product_uom_id.id,
                    'product_uom_qty': component.qty_to_buy if component.qty_to_buy < component.qty_available else component.qty_available,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'date': self.plan_date or datetime.now(),
                    'picking_type_id': self.picking_type_id.id,
                    'x_construction_line_ids': [(4, component.id)],
                }))

        if move_live:
            picking['move_ids_without_package'] = move_live

            stock_picking = self.env['stock.picking'].create(picking)

            stock_picking.action_assign()
        else:
            if self.state in ['order_received', 'progress']:
                raise UserError('手持数量がないため、出荷できませんでした。対象の構成品を正しい数量で購買発注してください。')

    def action_picking_from_warehouse(self):
        if not self.construction_component_ids.filtered(lambda x: x.qty_to_buy != 0 and x.product_id.type == 'product'):
            raise UserError('出荷するものは何もありません！')
        else:
            self._prepare_stock_picking()
