# -*- coding: utf-8 -*-

from odoo import models, fields, _


class SaleOrderApprovalWinzard(models.TransientModel):
    _name = 'sale.order.approval.winzard'

    sale_order_id = fields.Many2one('sale.order', string='Sale Quotation Id', required=True)
    x_deadline = fields.Date(string='承認希望日', required=True)
    x_comment = fields.Char(string='備考', required=False)
    # x_decision = fields.Char(string='決定', required=False)
    x_reason = fields.Char(string='理由', required=True)

    x_judgment = fields.Selection(
        string='判断',
        selection=[
            ('approval', 'Approval'),
            ('reject', 'Reject'),
            ('cancel', 'Cancel'),
        ],
        required=True, )

    def x_request_approval_action(self):
        print('request approval form')

    def x_decision_action(self):
        print('request approval form')
