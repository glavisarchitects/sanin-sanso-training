from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    x_construction_order_id = fields.Many2one('ss.erp.construction', string='工事オーダー', )
    has_construction_order_id = fields.Selection(
        related='category_id.has_construction_order_id', store=True)

    def write(self, vals):
        res = super(ApprovalRequest, self).write(vals)

        if self.x_construction_order_id and vals.get('status'):
            if vals.get('status') == 'approved':
                self.x_construction_order_id.sudo().write({'state': 'confirmed'})
            elif vals.get('status') == 'pending':
                self.x_construction_order_id.sudo().write({'state': 'request_approve'})
            elif vals.get('status') == 'refused':
                self.x_construction_order_id.sudo().write({'state': 'cancel'})

        return res
