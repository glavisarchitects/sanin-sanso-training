from odoo import fields, models, api, SUPERUSER_ID, _
from datetime import datetime
from itertools import groupby
from odoo.exceptions import UserError, ValidationError


class ConstructionComponent(models.Model):
    _name = 'ss.erp.construction.component'
    _description = '構成品'

    name = fields.Text(string='説明')
    product_id = fields.Many2one(comodel_name='product.product', string='プロダクト', tracking=True)
    product_uom_qty = fields.Float(string='数量', tracking=True, default=1.0)
    qty_to_invoice = fields.Float(string='請求対象', compute='_compute_qty_to_invoice')
    qty_invoiced = fields.Float(string='請求済み', compute='_get_invoice_qty')
    qty_to_buy = fields.Float(string='購買対象', compute='_compute_qty_to_buy')
    qty_bought = fields.Float(string='購買済み', compute='_compute_qty_bought')
    qty_reserved_from_warehouse = fields.Float(string='在庫出荷数', compute='_compute_qty_reserved_from_warehouse')

    @api.constrains("qty_bought", 'qty_reserved_from_warehouse', 'product_uom_qty')
    def _check_same_employee_number(self):
        for rec in self:
            if rec.product_uom_qty < rec.qty_bought + rec.qty_reserved_from_warehouse:
                raise ValidationError(_("消費数量が超過しています。構成品の数量が不足していないか確認してください。"))

    product_uom_id = fields.Many2one(comodel_name='uom.uom', string='単位', tracking=True,
                                     domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True, string='単位カテゴリ')
    partner_id = fields.Many2one(comodel_name='res.partner', domain=[('x_is_vendor', '=', True)], string='仕入先',
                                 tracking=True)
    payment_term_id = fields.Many2one(comodel_name='account.payment.term', string='支払条件', tracking=True)
    standard_price = fields.Monetary(string='仕入価格', tracking=True)
    currency_id = fields.Many2one('res.currency', '通貨', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    tax_id = fields.Many2one(comodel_name='account.tax', string='税', tracking=True)
    sale_price = fields.Monetary(string='販売価格', tracking=True)

    # @api.depends('margin_rate')
    # def _compute_sale_price(self):
    #     for rec in self:
    #         if rec.margin_rate!=0:
    #             rec.sale_price = rec.standard_price / (1 - rec.margin_rate)
    #
    # def _inverse_sale_price(self):
    #     for rec in self:
    #         if rec.sale_price:
    #             rec.margin_rate = abs(rec.standard_price / rec.sale_price - 1)

    margin = fields.Monetary(string='粗利益', store=True, compute='_compute_subtotal')
    # all_margin_rate = fields.Float(string='一律マージン率', related='construction_id.all_margin_rate')
    margin_rate = fields.Float(string='マージン(%)', store=True, default=lambda self: self._default_margin())
    subtotal_exclude_tax = fields.Monetary(string='小計（税別）', store=True, compute='_compute_subtotal')
    subtotal = fields.Monetary(string='小計', store=True, compute='_compute_subtotal')
    construction_id = fields.Many2one(comodel_name='ss.erp.construction', string='工事', ondelete='cascade')

    stock_move_ids = fields.Many2many(
        'stock.move',
        'construction_order_line_stock_move_rel',
        'construction_line_id', 'stock_move_id',
        string='在庫移動', readonly=True, copy=False)

    @api.depends('stock_move_ids.state')
    def _compute_qty_reserved_from_warehouse(self):
        for rec in self:
            reserved_qty = 0
            for line in rec.stock_move_ids:
                reserved_qty += line.reserved_availability
            rec.qty_reserved_from_warehouse = reserved_qty

    is_downpayment = fields.Boolean(
        string="頭金であるか", help="Down payments are made when creating invoices from a construction order.")

    state = fields.Selection(
        related='construction_id.state', string='工事ステータス', readonly=True, copy=False, store=True, default='draft')

    invoice_lines = fields.Many2many('account.move.line', 'construction_order_line_invoice_rel', 'order_line_id',
                                     'invoice_line_id', string='請求明細', copy=False)
    purchase_order_lines = fields.Many2many('purchase.order.line', 'construction_order_line_purchase_order_line_rel',
                                            'order_line_id',
                                            'po_line_id', string='購買明細', copy=False)

    onchange_sale_price = fields.Boolean(default=False, string='販売価格変更であるか')
    onchange_margin = fields.Boolean(default=False, string='マージン変更であるか')

    def _default_margin(self):
        return self.construction_id.all_margin_rate

    picking_type_id = fields.Many2one('stock.picking.type', related='construction_id.picking_type_id',
                                      store=True, string='オペレーションタイプ')
    location_id = fields.Many2one('stock.location', related='construction_id.location_id', store=True,
                                  string='構成品ロケーション')
    location_dest_id = fields.Many2one('stock.location', related='construction_id.location_dest_id', store=True,
                                       string='配送ロケーション')

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

    @api.model
    def default_get(self, fields):
        res = super(ConstructionComponent, self).default_get(fields)
        self.margin_rate = self.construction_id.all_margin_rate
        return res

    @api.depends('purchase_order_lines.order_id.state', 'purchase_order_lines.product_qty')
    def _compute_qty_bought(self):
        for rec in self:
            qty_bought = 0.0
            for line in rec.purchase_order_lines:
                if line.order_id.state != 'cancel':
                    qty_bought += line.product_qty
            rec.qty_bought = qty_bought

    @api.depends('product_uom_qty', 'tax_id', 'sale_price', 'standard_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal_exclude_tax = rec.product_uom_qty * rec.sale_price
            rec.subtotal = rec.subtotal_exclude_tax * (1 + rec.tax_id.amount / 100)
            rec.margin = (rec.sale_price - rec.standard_price) * rec.product_uom_qty

    def onchange(self, values, field_name, field_onchange):
        # OVERRIDE
        # As the dynamic lines in this model are quite complex, we need to ensure some computations are done exactly
        # at the beginning / at the end of the onchange mechanism. So, the onchange recursivity is disabled.
        return super(ConstructionComponent, self.with_context(recursive_onchanges=False)).onchange(values, field_name,
                                                                                                   field_onchange)

    @api.onchange('margin_rate')
    def _onchange_margin_rate(self):
        self.sale_price = self.standard_price / (1 - self.margin_rate)

    @api.onchange('sale_price', )
    def _onchange_sale_price(self):
        if self.sale_price != 0 and self.standard_price!=0:
            self.margin_rate = abs(self.standard_price / self.sale_price - 1)

    @api.onchange('standard_price')
    def _onchange_standard_price(self):
        self.sale_price = self.standard_price / (1 - self.margin_rate)

    # @api.onchange('margin_rate')
    # def _onchange_margin_rate(self):
    #     if not self.onchange_sale_price:
    #         self.sale_price = self.standard_price / (1 - self.margin_rate)
    #         self.onchange_margin = True
    #     else:
    #         self.onchange_margin = False
    #
    # @api.onchange('sale_price', )
    # def _onchange_sale_price(self):
    #     if not self.onchange_margin:
    #         self.margin_rate = abs(self.standard_price / self.sale_price - 1) if self.sale_price != 0 else 0
    #         self.onchange_sale_price = True
    #     else:
    #         self.onchange_sale_price = False
    #
    # @api.onchange('standard_price')
    # def _onchange_standard_price(self):
    #     self.sale_price = self.standard_price / (1 - self.margin_rate)
    #     self.onchange_margin = True
    #     self.onchange_sale_price = True

    def _compute_qty_to_invoice(self):
        for line in self:
            qty_invoiced = 0.0
            invoice_lines = self.env['account.move.line'].search(
                [('move_id.x_construction_order_id', '=', line.construction_id.id),
                 ('product_id', '=', line.product_id.id), ('product_uom_id', '=', line.product_uom_id.id)])
            for invoice_line in invoice_lines:
                if invoice_line.move_id.state != 'cancel':
                    if invoice_line.move_id.move_type == 'out_invoice':
                        qty_invoiced += invoice_line.quantity
                    elif invoice_line.move_id.move_type == 'out_refund':
                        qty_invoiced -= invoice_line.quantity
            line.qty_to_invoice = line.product_uom_qty - qty_invoiced

    def _prepare_purchase_order(self):
        company_id = self.env.user.company_id
        picking_type_id = self.env['stock.picking.type'].search(
            [('default_location_src_id.usage', '=', 'supplier'), ('default_location_dest_id.usage', '=', 'customer')],
            limit=1)
        return {
            'partner_id': self.partner_id.id,
            'user_id': self.env.user.id,
            'x_construction_order_id': self.construction_id.id,
            'picking_type_id': picking_type_id.id,
            'company_id': company_id.id,
            'currency_id': self.partner_id.with_company(
                company_id).property_purchase_currency_id.id or company_id.currency_id.id,
            'payment_term_id': self.payment_term_id.id,
            'date_order': datetime.today(),
            'x_rfq_issue_date': datetime.today(),
            'x_bis_categ_id': 'construction',
            'x_desired_delivery': 'full',
            'dest_address_id': self.construction_id.partner_id.id,
            'x_organization_id': self.construction_id.organization_id.id,
            'x_responsible_dept_id': self.construction_id.responsible_dept_id.id,
        }

    @api.onchange('product_id')
    def _onchange_component_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
            self.standard_price = self.product_id.product_tmpl_id.standard_price
            self.sale_price = self.product_id.product_tmpl_id.list_price
        direct_expense_fee_product = self.env.ref('ss_erp_construction.direct_expense_fee_product_data')
        direct_labo_fee_product = self.env.ref('ss_erp_construction.direct_labo_fee_product_data')
        direct_outsource_fee_product = self.env.ref('ss_erp_construction.direct_outsource_fee_product_data')
        indirect_expense_fee_product = self.env.ref('ss_erp_construction.indirect_expense_fee_product_data')
        indirect_material_fee_product = self.env.ref('ss_erp_construction.indirect_material_fee_product_data')
        indirect_labo_fee_product = self.env.ref('ss_erp_construction.indirect_labo_fee_product_data')
        indirect_outsource_fee_product = self.env.ref('ss_erp_construction.indirect_outsource_fee_product_data')

        # 間接経費計算
        if self.product_id.id == indirect_expense_fee_product.id:
            self.product_uom_qty = 1
            self.standard_price = sum(
                x.product_uom_qty * x.standard_price for x in self.construction_id.construction_component_ids.filtered(
                    lambda line: line.product_id.id == direct_expense_fee_product.id)) * 0.05

        # 間接材料費計算
        if self.product_id.id == indirect_material_fee_product.id:
            self.product_uom_qty = 1
            self.standard_price = sum(
                x.product_uom_qty * x.standard_price for x in self.construction_id.construction_component_ids.filtered(
                    lambda line: line.product_id.type == 'product')) * 0.00

        # 間接労務費計算
        if self.product_id.id == indirect_labo_fee_product.id:
            self.product_uom_qty = 1
            self.standard_price = sum(
                x.product_uom_qty * x.standard_price for x in self.construction_id.construction_component_ids.filtered(
                    lambda line: line.product_id.id == direct_labo_fee_product.id)) * 0.05

        if self.product_id.id == indirect_outsource_fee_product.id:
            self.product_uom_qty = 1
            self.standard_price = sum(
                x.product_uom_qty * x.standard_price for x in self.construction_id.construction_component_ids.filtered(
                    lambda line: line.product_id.id == direct_outsource_fee_product.id)) * 0.05

    @api.depends('product_uom_qty', 'qty_reserved_from_warehouse', 'qty_bought', )
    def _compute_qty_to_buy(self):
        for rec in self:
            if rec.product_id.type != 'consu':
                rec.qty_to_buy = rec.product_uom_qty - rec.qty_reserved_from_warehouse - rec.qty_bought
            else:
                rec.qty_to_buy = 0

    # def calculate_qty_to_buy(self):
    #     if self.product_id.type == "product":
    #         quantity = 0
    #         for picking in self.construction_id.picking_ids:
    #             # 在庫出荷の量の計算
    #             if picking.picking_type_id.code == 'outgoing':
    #                 quantity += sum(picking.move_line_ids_without_package.filtered(
    #                     lambda l: l.product_id == self.product_id and l.product_uom_id == self.product_uom_id).mapped(
    #                     'product_uom_qty')) \
    #                             + sum(picking.move_line_ids_without_package.filtered(
    #                     lambda l: l.product_id == self.product_id and l.product_uom_id == self.product_uom_id).mapped(
    #                     'qty_done'))
    #
    #         domain = [
    #             ('partner_id', '=', self.partner_id.id),
    #             ('state', '!=', 'cancel'),
    #             ('payment_term_id', '=', self.payment_term_id.id),
    #             ('x_construction_order_id', '=', self.construction_id.id),
    #         ]
    #         po_ids = self.env['purchase.order'].sudo().search(domain).order_line.filtered(
    #             lambda x: x.product_id == self.product_id)
    #         quantity += sum(po_ids.mapped('product_qty'))
    #         return self.product_uom_qty - quantity
    #     elif self.product_id.type == "service":
    #         domain = [
    #             ('partner_id', '=', self.partner_id.id),
    #             ('state', '!=', 'cancel'),
    #             ('payment_term_id', '=', self.payment_term_id.id),
    #             ('x_construction_order_id', '=', self.construction_id.id),
    #         ]
    #         po_ids = self.env['purchase.order'].sudo().search(domain).order_line.filtered(
    #             lambda x: x.product_id == self.product_id)
    #         return self.product_uom_qty - sum(po_ids.mapped('product_qty'))
    #     else:
    #         return 0

    @api.model
    def _run_buy(self):
        qty_to_buy = self.qty_to_buy
        if qty_to_buy != 0 and self.product_id.type != "consu" and self.partner_id:
            domain = [
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'draft'),
                ('payment_term_id', '=', self.payment_term_id.id),
                ('x_construction_order_id', '=', self.construction_id.id),
            ]
            po = self.env['purchase.order'].sudo().search(domain, limit=1)
            if not po:
                vals = self._prepare_purchase_order()
                po = self.env['purchase.order'].sudo().create(vals)

            po_line = po.order_line.filtered(
                lambda
                    l: not l.display_type and l.product_uom == self.product_uom_id and l.product_id == self.product_id)

            if po_line:
                line_ids = po_line.construction_line.ids
                line_ids.append(self.id)
                vals = {'product_qty': po_line.product_qty + qty_to_buy,
                        'construction_line': [(6, 0, line_ids)]
                        }
                po_line[0].write(vals)
            else:
                po_line_values = {
                    'order_id': po.id,
                    'product_id': self.product_id.id,
                    'product_qty': qty_to_buy,
                    'product_uom': self.product_uom_id.id,
                    'price_unit': self.standard_price,
                    'construction_line': [(4, self.id)]
                }
                self.env['purchase.order.line'].sudo().create(po_line_values)
            return po
        else:
            return False

    def _prepare_invoice_line(self, **optional_values):
        """
        Prepare the dict of values to create the new invoice line for a construction order line.

        :param qty: float quantity to invoice
        :param optional_values: any parameter that should be added to the returned invoice line
        """
        self.ensure_one()
        res = {
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom_id.id,
            'quantity': self.qty_to_invoice,
            'price_unit': self.sale_price,
            'construction_line_ids': [(4, self.id)],
            'tax_ids': [(6, 0, [self.tax_id.id])] if self.tax_id else False,
        }
        if optional_values:
            res.update(optional_values)
        return res

    @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity')
    def _get_invoice_qty(self):
        """
        Compute the quantity invoiced. If case of a refund, the quantity invoiced is decreased. Note
        that this is the case only if the refund is generated from the SO and that is intentional: if
        a refund made would automatically decrease the invoiced quantity, then there is a risk of reinvoicing
        it automatically, which may not be wanted at all. That's why the refund has to be created from the SO
        """
        for line in self:
            qty_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.move_id.state != 'cancel':
                    if invoice_line.move_id.move_type == 'out_invoice':
                        qty_invoiced += invoice_line.product_uom_id._compute_quantity(invoice_line.quantity,
                                                                                      line.product_uom_id)
                    elif invoice_line.move_id.move_type == 'out_refund':
                        qty_invoiced -= invoice_line.product_uom_id._compute_quantity(invoice_line.quantity,
                                                                                      line.product_uom_id)
            line.qty_invoiced = qty_invoiced

    @api.depends('qty_invoiced', 'product_uom_qty')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:
            line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
