# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = 'res.users'

    organization_ids = fields.Many2many('ss_erp.organization', string="組織")
    dep_ids = fields.Many2many('ss_erp.responsible.department', string="部署")
