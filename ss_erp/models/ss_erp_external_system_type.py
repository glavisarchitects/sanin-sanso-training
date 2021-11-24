# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ExternalSystemType(models.Model):
    _name = 'ss_erp.external.system.type'
    _description = 'External System Type'

    name = fields.Char('External system type name', index=True, required=True)
    code = fields.Char(string='Code', index=True, required=True)