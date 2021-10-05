# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TransactionClassification(models.Model):
    _inherit = 'x.transaction.classification'

    code = fields.Char('Code')
