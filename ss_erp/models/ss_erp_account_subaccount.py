# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountSubAccount(models.Model):
    _name = 'ss_erp.account.subaccount'
    _description = 'Account Sub Account'

    name = fields.Char(string='Name', index=True, required=True)
    code = fields.Char(string='Code', index=True, required=True)
