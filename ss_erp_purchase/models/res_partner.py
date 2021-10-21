# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_email_quote_request = fields.Char("E-mail address for sending a quote request", copy=False)
    x_email_purchase = fields.Char("Purchase order sending email address", copy=False)
