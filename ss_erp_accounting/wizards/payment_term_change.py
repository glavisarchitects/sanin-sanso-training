# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PaymentTermChangeWizard(models.TransientModel):
    _name = 'payment.term.change.wizard'
    _description = 'Payment Term Change'

    invoice_payment_term_id = fields.Many2one('account.payment.term', string='支払サイト')

    def payment_term_change(self):
        if self._context.get('active_model') == 'account.move':
            lines = self.env['account.move'].browse(self._context.get('active_ids', []))
            for line in lines:
                line.invoice_payment_term_id = self.invoice_payment_term_id
                line.sudo()._recompute_payment_terms_lines()
            