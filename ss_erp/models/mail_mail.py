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
                if email:
                    email_to = [tools.formataddr((partner.name or 'False', email))]
            else:
                email_to = tools.email_split_and_format(self.email_to)
            res.update({'email_to': email_to})
        return res


class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'

    def send_email(
            self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
            smtp_user=None, smtp_password=None, smtp_encryption=None, smtp_debug=False,
            smtp_session=None):
        override_email = self.env['ir.config_parameter'].sudo().get_param(
            'ss_erp.override_email_from', False)
        if override_email:
            for field in ['from', 'reply-to']:
                if not message[field]:
                    continue
                # TODO: compute value
                del message[field]
                message[field] = override_email
        else:
            del message['reply-to']
        return super(IrMailServer, self).send_email(
            message, mail_server_id=mail_server_id,
            smtp_server=smtp_server, smtp_port=smtp_port, smtp_user=smtp_user,
            smtp_password=smtp_password, smtp_encryption=smtp_encryption,
            smtp_debug=smtp_debug, smtp_session=smtp_session)