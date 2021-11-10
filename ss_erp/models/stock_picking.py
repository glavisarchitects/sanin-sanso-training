# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_account_modify = fields.Boolean(
        "Inventory journal correction", index=True)
    x_dest_address_info = fields.Html("Direct shipping address")
    x_organization_id = fields.Many2one(
        'ss_erp.organization', string="Organization in charge")
    x_responsible_dept_id = fields.Many2one(
        'ss_erp.responsible.department', string="Jurisdiction")
    x_mkt_user_id = fields.Many2one(
        'res.users', string="Sales staff")
    # TODO
    # x_so_type = fields.Selection(related='sale_id.x_so_type', string="Sales type" )
    x_import_id = fields.Char("Capture ID", copy=False)
    location_dest_id_usage = fields.Selection(
        related='location_dest_id.usage', string='Destination Location Type', readonly=True)
