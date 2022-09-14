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
    x_construction_template_id = fields.Many2one('construction.template', string='工事テンプレート', )
    has_construction_template_id = fields.Selection(
        related='category_id.has_construction_template_id', store=True)

    def _validate_request(self):
        super()._validate_request()

        if self.x_construction_order_id:
            if self.request_status == 'approved':
                self.x_construction_order_id.sudo().write({'state': 'confirmed'})
            elif self.request_status == 'pending':
                self.x_construction_order_id.sudo().write({'state': 'request_approve'})
            elif self.request_status == 'refused':
                self.x_construction_order_id.sudo().write({'state': 'cancel'})

        if self.x_construction_template_id:
            self.x_construction_template_id.update({'state': self.request_status})

