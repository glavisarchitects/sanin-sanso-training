from odoo import fields, models, api


class ConstructionComponent(models.Model):
    _name = 'ss.erp.construction.component'
    _description = '構成品'

    product_id = fields.Many2one(comodel_name='product.product', string='プロダクト', tracking=True)
    product_uom_qty = fields.Float(string='数量', tracking=True)
    # qty_reserved = fields.Float(string='引当済み', compute='_compute_quantity', store=True)
    # qty_done = fields.Float(string='消費済み', compute='_compute_quantity', store=True)
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
        string="Is a down payment", help="Down payments are made when creating invoices from a sales order."
        " They are not copied when duplicating a sales order.")

    # invoice_lines = fields.Many2many('account.move.line', 'sale_order_line_invoice_rel', 'order_line_id',
    # 'invoice_line_id', string='Invoice Lines', copy=False)
    invoice_status = fields.Selection([
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
        ], string='Invoice Status', compute='_compute_invoice_status', store=True, readonly=True, default='no')

    state = fields.Selection(
        related='construction_id.state', string='工事ステータス', readonly=True, copy=False, store=True, default='draft')

    # @api.depends('construction_id.picking_ids', 'construction_id.move_ids.reserved_availability',
    #              'construction_id.move_ids.quantity_done')
    # def _compute_quantity(self):
    #     for line in self:
    #         product_move_ids = line.construction_id.move_ids.filtered(
    #             lambda x: x.product_id.id == line.product_id.id and x.product_uom.id == line.product_uom_id.id)
    #         line.qty_reserved = sum([m.reserved_availability for m in product_move_ids])
    #         line.qty_done = sum([m.quantity_done for m in product_move_ids])

    @api.depends('sale_price', 'construction_id.all_margin_rate', 'tax_id')
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

    # @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    # def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO line. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: we refer to the quantity to invoice of the line. Refer to method
          `_get_to_invoice_qty()` for more information on how this quantity is calculated.
        - upselling: this is possible only for a product invoiced on ordered quantities for which
          we delivered more than expected. The could arise if, for example, a project took more
          time than expected but we decided not to invoice the extra cost to the client. This
          occurs onyl in state 'sale', so that when a SO is set to done, the upselling opportunity
          is removed from the list.
        - invoiced: the quantity invoiced is larger or equal to the quantity ordered.
        """
        # precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        # for line in self:
        #     if line.state not in ('sale', 'done'):
        #         line.invoice_status = 'no'
        #     elif line.is_downpayment and line.untaxed_amount_to_invoice == 0:
        #         line.invoice_status = 'invoiced'
        #     elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
        #         line.invoice_status = 'to invoice'
        #     elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and\
        #             line.product_uom_qty >= 0.0 and\
        #             float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
        #         line.invoice_status = 'upselling'
        #     elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
        #         line.invoice_status = 'invoiced'
        #     else:
        #         line.invoice_status = 'no'


