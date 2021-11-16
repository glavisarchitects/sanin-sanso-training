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

    x_inspection_user_id = fields.Many2one(
        comodel_name='res.users',
        string='良品検査担当者名',
        required=False)

    x_inspection_exist = fields.Boolean(
        string='良品検査実施有無',
        default=False)

    has_lot_ids = fields.Boolean(
        'Has Serial Numbers', compute='_compute_has_lot_ids')

    @api.depends('move_ids_without_package', 'move_ids_without_package.lot_ids')
    def _compute_has_lot_ids(self):
        for record in self:
            record.has_lot_ids = True if len(record.move_ids_without_package.mapped(
                'lot_ids')) else False


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    x_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='連絡先名',
        required=False)