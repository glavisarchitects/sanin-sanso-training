# -*- coding: utf-8 -*-

from odoo import models,fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_fb_created = fields.Boolean(string='FB作成済みフラグ', required=True, default=False)