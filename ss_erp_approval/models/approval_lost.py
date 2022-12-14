# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ApprovalLost(models.TransientModel):
    _name = 'ss_erp.approval.lost'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '却下理由'

    lost_reason = fields.Char('却下理由')

    def action_lost_reason_apply(self):
        request = self.env['approval.request'].browse(self.env.context.get('active_ids'))
        request.sudo().write({'x_reject': self.lost_reason})
        return request.sudo().action_refuse()
