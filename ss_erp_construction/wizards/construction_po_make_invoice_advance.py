# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class ConstructionPurchaseAdvancePaymentInv(models.TransientModel):
    _name = "ss_erp.construction.po.advance.payment.inv"
    _description = "Construction Purchase Advance Payment Invoice"

    @api.model
    def _count(self):
        return len(self._context.get('active_ids', []))

    @api.model
    def _default_product_id(self):
        po_ids = self.env['purchase.order'].browse(self._context.get('active_ids', []))
        if len(po_ids.filtered(lambda x: x.x_bis_categ_id == 'construction')) > 0:
            downpayment_product_id = self.env['ir.config_parameter'].sudo().get_param(
                'ss_erp_po_construction_downpayment_default_product_id')
            downpayment_product_product = self.env['product.product'].search([('product_tmpl_id', '=', int(downpayment_product_id))])
            if not downpayment_product_id or not downpayment_product_product:
                raise UserError(
                    "工事用の前払プロダクトの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(ss_erp_po_construction_downpayment_default_product_id)")

        else:
            downpayment_product_id = self.env['ir.config_parameter'].sudo().get_param(
                'ss_erp_po_downpayment_default_product_id')
            downpayment_product_product = self.env['product.product'].search(
                [('product_tmpl_id', '=', int(downpayment_product_id))])
            if not downpayment_product_product:
                raise UserError(
                    "前払プロダクトの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(ss_erp_po_downpayment_default_product_id)")
        return self.env['product.product'].browse(downpayment_product_product.id)

    @api.model
    def _default_deposit_account_id(self):
        po_ids = self.env['purchase.order'].browse(self._context.get('active_ids', []))
        product_id = self._default_product_id()

        if len(po_ids.filtered(lambda x: x.x_bis_categ_id == 'construction')) > 0:
            return product_id._get_product_accounts()['construction_expense']
        else:
            return product_id._get_product_accounts()['expense']

    @api.model
    def _default_deposit_taxes_id(self):
        return self._default_product_id().supplier_taxes_id

    @api.model
    def _default_has_down_payment(self):
        if self._context.get('active_model') == 'purchase.order' and self._context.get('active_id', False):
            purchase_order = self.env['purchase.order'].browse(self._context.get('active_id'))
            return purchase_order.order_line.filtered(lambda line: line.is_downpayment)
        return False

    @api.model
    def _default_currency_id(self):
        if self._context.get('active_model') == 'purchase.order' and self._context.get('active_id', False):
            purchase_order = self.env['purchase.order'].browse(self._context.get('active_id'))
            return purchase_order.currency_id

    advance_payment_method = fields.Selection([
        ('delivered', '通常の請求書'),
        ('percentage', '前払金 (パーセント)'),
        ('fixed', '前払金 (固定金額)')
    ], string='請求書作成', default='delivered', required=True, )
    deduct_down_payments = fields.Boolean('頭金を差し引く', default=True)
    has_down_payments = fields.Boolean('頭金がある', default=_default_has_down_payment, readonly=True)
    product_id = fields.Many2one('product.product', string='前受金', domain=[('type', '=', 'service')],
                                 default=_default_product_id)
    amount = fields.Float('前受金額', digits='Account', help="事前に請求される金額の割合。税金は含まれていません。")
    currency_id = fields.Many2one('res.currency', string='通貨', default=_default_currency_id)
    fixed_amount = fields.Monetary('頭金(固定)', help="事前に請求される定額(税抜き)。")
    deposit_account_id = fields.Many2one("account.account", string="収益勘定", domain=[('deprecated', '=', False)],
                                         help="預金用口座", default=_default_deposit_account_id)
    deposit_taxes_id = fields.Many2many("account.tax", string="顧客税", help="預金に使用される税金",
                                        default=_default_deposit_taxes_id)
    count = fields.Integer(default=_count, string='オーダ数')

    @api.onchange('advance_payment_method')
    def onchange_advance_payment_method(self):
        if self.advance_payment_method == 'percentage':
            amount = self.default_get(['amount']).get('amount')
            return {'value': {'amount': amount}}
        return {}

    def _prepare_invoice_values(self, order, name, amount, order_line):
        head_office_organization = self.env['ss_erp.organization'].search([('organization_code', '=', '00000')],
                                                                          limit=1)
        invoice_vals = {
            'ref': order.partner_ref or False,
            'move_type': 'in_invoice',
            'invoice_origin': order.name,
            'x_organization_id': head_office_organization.id, #TODO: 確認必要
            'x_responsible_dept_id': order.x_responsible_dept_id.id,
            'x_business_organization_id': order.x_organization_id.id,
            'x_construction_order_id': order.x_construction_order_id.id,
            'invoice_user_id': order.user_id.id,
            'partner_id': order.partner_id.id,
            'purchase_id': order.id,
            'x_responsible_user_id': order.user_id.id,
            'fiscal_position_id': (order.fiscal_position_id or order.fiscal_position_id.get_fiscal_position(
                order.partner_id.id)).id,
            'partner_shipping_id': order.partner_id.id,
            'currency_id': order.currency_id.id,
            'invoice_payment_term_id': order.payment_term_id.id,
            'partner_bank_id': order.partner_id.bank_ids[:1].id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'price_unit': amount,
                'quantity': 1.0,
                'product_id': self.product_id.id,
                'product_uom_id': order_line.product_uom.id,
                'purchase_line_id': order_line.id,
                'tax_ids': [(6, 0, order_line.taxes_id.ids)],
            })],
        }

        return invoice_vals

    def _get_advance_details(self, order):
        if self.advance_payment_method == 'percentage':
            if all(self.product_id.taxes_id.mapped('price_include')):
                amount = order.amount_total * self.amount / 100
            else:
                amount = order.amount_untaxed * self.amount / 100
            name = _("%s%% の前払金") % (self.amount)
        else:
            amount = self.fixed_amount
            name = _('前払金')

        return amount, name

    def _create_invoice(self, order, order_line, amount):
        journal = self.env['account.journal'].search([('type', '=', 'purchase'), ('x_is_construction', '=', True)],
                                                     limit=1)
        if not journal:
            raise UserError('工事購買の仕訳帳は設定していません。もう一度ご確認ください')

        if (self.advance_payment_method == 'percentage' and self.amount <= 0.00) or (
                self.advance_payment_method == 'fixed' and self.fixed_amount <= 0.00):
            raise UserError(_('前受金の金額は正の値でなければなりません。'))

        amount, name = self._get_advance_details(order)

        invoice_vals = self._prepare_invoice_values(order, name, amount, order_line)

        if order.fiscal_position_id:
            invoice_vals['fiscal_position_id'] = order.fiscal_position_id.id

        invoice_vals['journal_id'] = journal.id

        invoice = self.env['account.move'].with_company(order.company_id) \
            .sudo().create(invoice_vals).with_user(self.env.uid)
        return invoice

    def _prepare_po_line(self, order, analytic_tag_ids, tax_ids, amount):
        context = {'lang': order.partner_id.lang}
        po_values = {
            'name': _('前払金: %s') % (time.strftime('%Y年%m月%d日'),),
            'price_unit': amount,
            'product_qty': 0.0,
            'order_id': order.id,
            'date_planned': datetime.now(),
            'product_uom': self.product_id.uom_id.id,
            'product_id': self.product_id.id,
            'analytic_tag_ids': analytic_tag_ids,
            'taxes_id': [(6, 0, tax_ids)],
            'is_downpayment': True,
            'sequence': order.order_line and order.order_line[-1].sequence + 1 or 10,
        }
        del context
        return po_values

    def create_invoices(self):
        purchase_order_ids = self.env['purchase.order'].browse(self._context.get('active_ids', []))

        if self.advance_payment_method == 'delivered':
            moves = purchase_order_ids._create_invoices(final=self.deduct_down_payments)
        else:
            purchase_order_line_obj = self.env['purchase.order.line']
            for purchase_order in purchase_order_ids:
                amount, name = self._get_advance_details(purchase_order)

                taxes = self.product_id.taxes_id.filtered(
                    lambda r: not purchase_order.company_id or r.company_id == purchase_order.company_id)
                tax_ids = purchase_order.fiscal_position_id.map_tax(taxes, self.product_id,
                                                                    purchase_order.partner_id).ids
                analytic_tag_ids = []
                for line in purchase_order.order_line:
                    analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

                po_line_values = self._prepare_po_line(purchase_order, analytic_tag_ids, tax_ids, amount)
                po_line = purchase_order_line_obj.create(po_line_values)
                moves = self._create_invoice(purchase_order, po_line, amount)
        if self._context.get('open_invoices', False):
            return purchase_order_ids.action_view_invoice(moves)
        return {'type': 'ir.actions.act_window_close'}
