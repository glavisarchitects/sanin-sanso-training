from odoo import fields, models, api, SUPERUSER_ID, _
from datetime import datetime
from itertools import groupby
from odoo.exceptions import UserError


class ConstructionComponent(models.Model):
    _name = 'ss.erp.construction.component'
    _description = '構成品'

    name = fields.Text(string='説明')
    product_id = fields.Many2one(comodel_name='product.product', string='プロダクト', tracking=True)
    product_uom_qty = fields.Float(string='数量', tracking=True, default=1.0)
    qty_done = fields.Float(string='消費済み', store=True)
    qty_to_invoice = fields.Float(string='請求対象', compute='_compute_qty_to_invoice')
    # qty_to_buy = fields.Float(string='購買対象', compute='_compute_qty_to_buy')
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
    margin = fields.Monetary(string='粗利益', compute='_compute_margin', store=True)
    margin_rate = fields.Float(string='マージン(%)', compute='_compute_margin', store=True)
    subtotal_exclude_tax = fields.Monetary(string='小計（税別）', compute='_compute_margin', store=True)
    subtotal = fields.Monetary(string='小計', compute='_compute_margin', store=True)
    construction_id = fields.Many2one(comodel_name='ss.erp.construction', string='工事')

    is_downpayment = fields.Boolean(
        string="頭金であるか", help="Down payments are made when creating invoices from a construction order.")

    state = fields.Selection(
        related='construction_id.state', string='工事ステータス', readonly=True, copy=False, store=True, default='draft')

    @api.depends('sale_price', 'construction_id.all_margin_rate', 'tax_id', 'standard_price', 'product_uom_qty')
    def _compute_margin(self):
        for rec in self:
            if rec.construction_id.all_margin_rate != 0:
                rec.margin_rate = rec.construction_id.all_margin_rate
                rec.sale_price = rec.standard_price * (1 + rec.margin_rate)
                rec.margin = (rec.sale_price - rec.standard_price) * rec.product_uom_qty
            else:
                rec.margin_rate = rec.sale_price / rec.standard_price - 1 if rec.standard_price != 0 else 1
                rec.margin = (rec.sale_price - rec.standard_price) * rec.product_uom_qty
            rec.subtotal_exclude_tax = rec.product_uom_qty * rec.sale_price
            rec.subtotal = rec.subtotal_exclude_tax * (1 + rec.tax_id.amount / 100)

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
            'user_id': False,
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
            self.standard_price = sum(x.product_uom_qty * x.standard_price for x in self.construction_id.construction_component_ids.filtered(
                lambda line: line.product_id.id == direct_expense_fee_product.id)) * 0.05

        # 間接材料費計算
        if self.product_id.id == indirect_material_fee_product.id:
            self.product_uom_qty = 1
            self.standard_price = sum(x.product_uom_qty * x.standard_price for x in self.construction_id.construction_component_ids.filtered(
                lambda line: line.product_id.type == 'product')) * 0.00

        # 間接労務費計算
        if self.product_id.id == indirect_labo_fee_product.id:
            self.product_uom_qty = 1
            self.standard_price = sum(x.product_uom_qty * x.standard_price for x in self.construction_id.construction_component_ids.filtered(
                lambda line: line.product_id.id == direct_labo_fee_product.id)) * 0.05

        if self.product_id.id == indirect_outsource_fee_product.id:
            self.product_uom_qty = 1
            self.standard_price = sum(x.product_uom_qty * x.standard_price for x in self.construction_id.construction_component_ids.filtered(
                lambda line: line.product_id.id == direct_outsource_fee_product.id)) * 0.05

    def calculate_qty_to_buy(self):
        if self.product_id.type == "product":
            quantity = 0
            for picking in self.construction_id.picking_ids:
                # 在庫出荷の量の計算
                if picking.picking_type_id.code == 'outgoing':
                    quantity += sum(picking.move_line_ids_without_package.filtered(
                        lambda l: l.product_id == self.product_id and l.product_uom_id == self.product_uom_id).mapped(
                        'product_uom_qty')) \
                                + sum(picking.move_line_ids_without_package.filtered(
                        lambda l: l.product_id == self.product_id and l.product_uom_id == self.product_uom_id).mapped(
                        'qty_done'))

                picking_type_id = self.env['stock.picking.type'].search(
                    [('default_location_src_id.usage', '=', 'supplier'),
                     ('default_location_dest_id.usage', '=', 'customer')],
                    limit=1)

                # 直送数量の計算
                if picking.picking_type_id == picking_type_id:
                    quantity += sum(picking.move_ids_without_package.filtered(
                        lambda l: l.product_id == self.product_id and l.product_uom == self.product_uom_id).mapped(
                        'product_uom_qty'))

            return self.product_uom_qty - quantity
        else:
            return 0

    @api.model
    def _run_buy(self):
        qty_to_buy = self.calculate_qty_to_buy()
        if qty_to_buy != 0 and self.product_id.type == "product":
            if not self.partner_id:
                raise UserError("%sのプロダクトに対して、仕入先は設定してください。" % self.product_id.name)

            domain = [
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'draft'),
                ('x_construction_order_id', '=', self.construction_id.id),
            ]
            po = self.env['purchase.order'].sudo().search(domain, limit=1)
            if not po:
                vals = self._prepare_purchase_order()
                po = self.env['purchase.order'].with_user(SUPERUSER_ID).create(vals)

            po_line = po.order_line.filtered(
                lambda
                    l: not l.display_type and l.product_uom == self.product_uom_id and l.product_id == self.product_id)

            if po_line:
                vals = {'product_qty': po_line.product_qty + qty_to_buy}
                po_line[0].write(vals)
            else:
                po_line_values = {
                    'order_id': po.id,
                    'product_id': self.product_id.id,
                    'product_qty': qty_to_buy,
                    'product_uom': self.product_uom_id.id
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
            'tax_ids': [(6, 0, [self.tax_id.id])] if self.tax_id else False,
        }
        if optional_values:
            res.update(optional_values)
        return res
