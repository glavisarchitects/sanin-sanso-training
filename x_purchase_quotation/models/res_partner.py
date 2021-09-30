# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    email_quote_request = fields.Char("E-mail address for sending a quote request", copy=False)
    email_purchase = fields.Char("Purchase order sending email address", copy=False)

    # def read(self, list_fields=None, load='_classic_read'):
    #     if 'partner_email_field' in self._context:
    #         partner_email_field = self._context.get('partner_email_field')
    #         list_fields += [partner_email_field]
    #         res = super(ResPartner, self).read(list_fields, load)
    #         for r in res:
    #             r['email'] = r[partner_email_field]

    #         return res
    #     res = super(ResPartner, self).read(list_fields, load)
    #     return res
