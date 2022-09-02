# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    x_sub_account_ids = fields.One2many(
        comodel_name='ss_erp.account.subaccount',
        inverse_name='account_account_id',
        string='補助科目',
        required=False)
