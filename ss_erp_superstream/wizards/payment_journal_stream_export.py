# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round, float_is_zero
from datetime import datetime
import base64
import calendar


class PaymentJournalStreamExport(models.TransientModel):
    _name = 'payment.journal.stream.export'

    first_day_period = fields.Date(string='First Day')
    last_day_period = fields.Date(string='Last Day')
    branch_id = fields.Many2one('ss_erp.organization', string='支店')

    def payment_journal_stream_export(self):
        pass