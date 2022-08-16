# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PostDifferenceAccount(models.TransientModel):
    _name = 'ss_erp.post.difference.account'
    _description = 'Post Difference Account'

    acc_payment_register_id = fields.Many2one('account.payment.register')

    currency_id = fields.Many2one(related='acc_payment_register_id.currency_id', help="The payment's line currency.")
    payment_money = fields.Monetary(store=True, string='Payment of Money')
    writeoff_account_id = fields.Many2one('account.account', string="Account", copy=False, )
    writeoff_label = fields.Char(string='Label', default='Write-Off',
                                 help='Change label of the counterpart that will hold the payment difference')
