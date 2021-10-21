# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_fax_number = fields.Char(
        string="Fax Number", size=20
    )
    organization_id = fields.Many2one('ss_erp.organization', string='Organization')

