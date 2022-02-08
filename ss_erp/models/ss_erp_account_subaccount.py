# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountSubAccount(models.Model):
    _name = 'ss_erp.account.subaccount'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '補助科目'

    name = fields.Char(string='補助科目名', index=True)
    code = fields.Char(string='コード', index=True)
