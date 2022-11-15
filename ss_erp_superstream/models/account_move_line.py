# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_super_stream_linked = fields.Boolean('SuperStream連携済', index=True, default=False)
