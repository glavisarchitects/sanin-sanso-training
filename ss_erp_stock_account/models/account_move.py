# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_account_modify = fields.Boolean(
        "在庫仕訳訂正", index=True)
    