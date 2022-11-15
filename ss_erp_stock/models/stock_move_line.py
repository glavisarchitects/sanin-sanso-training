# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    x_partner_id = fields.Many2one(
        'res.users', string="連絡先名", required=False, )
    x_organization_id = fields.Many2one('ss_erp.organization',
                                        string='組織名', store=True)

    @api.model
    def create(self, vals):
        result = super(StockMoveLine, self).create(vals)
        if result.picking_id:
            result.update({'x_partner_id': result.picking_id.partner_id.id})
        return result
