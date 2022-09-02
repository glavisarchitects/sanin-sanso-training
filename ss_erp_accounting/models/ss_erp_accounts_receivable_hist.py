# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountsReceivableHist(models.Model):
    _name = 'ss_erp.accounts.receivable.hist'

    organization_id = fields.Many2one('ss_erp.organization', index=True, string='組織')
    target_date = fields.Date(index=True, string='対象年月')
    partner_id = fields.Many2one('res.partner', '得意先')

    # Todo: confirm the data type of the fields below
    prev_month_balance = fields.Float('前月残高')
    correction = fields.Float('訂正')
    payment = fields.Float('入金')
    carry_forward = fields.Float('繰越')
    sales = fields.Float('売上')
    tax = fields.Many2one('account.tax', 'tax')
    balance = fields.Float('当月残高')
    payment_site = fields.Char('支払サイト')
    payment_method = fields.Selection([
        ('paypal', "PayPal"),
        ('stripe', "Credit card (via Stripe)"),
        ('other', "Other payment acquirer"),
        ('manual', "Custom payment instructions"),
    ], string="支払方法",)
    date = fields.Date('締め日')