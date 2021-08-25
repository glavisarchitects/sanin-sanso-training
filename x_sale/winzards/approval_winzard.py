# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ApprovalWinzard(models.TransientModel):
    _name = 'approval.winzard'
    _desc = 'Sale Approval Winzard'

    x_from_request = fields.Char(string='Request from')
    x_expect_date = fields.Date(string='Expect Date', default=fields.Date.today, required=True)

    def sample_name(self):
        print('welcome to approval winzard')
