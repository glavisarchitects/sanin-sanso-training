# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    x_no_need_save = fields.Boolean(default=False, string="Use for download only, Will delete it soon")
