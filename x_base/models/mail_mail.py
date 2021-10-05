# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import tools

import logging

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = 'mail.mail'

    def _send_prepare_values(self, partner=None):
        res = super(MailMail, self)._send_prepare_values(partner)
        if 'partner_email_field' in self._context:
            if partner:
                email = getattr(partner, self._context.get(
                    'partner_email_field'))
                email_to = [tools.formataddr((partner.name or 'False', email))]
            else:
                email_to = tools.email_split_and_format(self.email_to)
            res.update({'email_to': email_to})
        return res
