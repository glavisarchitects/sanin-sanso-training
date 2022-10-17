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

    x_construction_order_id2 = fields.Many2one('ss.erp.construction', string='工事見積書', )
    has_construction_order_id2 = fields.Selection(
        related='category_id.has_construction_order_id2', store=True)
    x_construction_template_id = fields.Many2one('construction.template', string='工事テンプレート', )
    has_construction_template_id = fields.Selection(
        related='category_id.has_construction_template_id', store=True)

    def _validate_request(self):
        super()._validate_request()

        if self.x_construction_order_id:
            self.x_construction_order_id.sudo().write({'validate_approval_status': self.request_status})

        if self.x_construction_order_id2:
            self.x_construction_order_id2.sudo().write({'estimate_approval_status': self.request_status})

        if self.x_construction_template_id:
            self.x_construction_template_id.sudo().update({'state': self.request_status})

