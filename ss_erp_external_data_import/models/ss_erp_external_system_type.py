# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ExternalSystemType(models.Model):
    _name = 'ss_erp.external.system.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '外部システム種別'

    name = fields.Char('外部システム種別名', index=True, )
    code = fields.Char(string='コード', index=True,)
    active = fields.Boolean(default=True, )