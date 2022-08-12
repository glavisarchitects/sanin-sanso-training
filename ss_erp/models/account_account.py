# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    x_sub_account_ids = fields.Many2many('ss_erp.account.subaccount', 'account_subaccount_rel',
                                         string='補助科目名')
