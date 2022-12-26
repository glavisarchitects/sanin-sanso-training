# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountSubAccount(models.Model):
    _name = 'ss_erp.account.subaccount'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '補助科目'
    _rec_name = 'display_name'

    name = fields.Char(string='補助科目名', index=True, required=True)
    code = fields.Char(string='コード', index=True, required=True)
    display_name = fields.Char(string='表示名', compute='_compute_display_name', store=True)

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s %s' % (rec.code, rec.name)
