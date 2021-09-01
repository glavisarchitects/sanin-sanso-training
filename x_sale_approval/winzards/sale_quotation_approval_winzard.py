# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class SaleQuotationApprovalWinzard(models.TransientModel):
    _name = 'sale.quotation.approval.winzard'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    crm_team_id = fields.Many2one("crm.team", string="申請先", required=True)
    x_deadline = fields.Date(string='承認希望日', required=False, default=fields.Date.today)
    x_comment = fields.Char(string='備考', required=False, help='comment')
    x_reason = fields.Char(string='理由', required=False, help='reason')

    x_state = fields.Selection(
        string='判断',
        selection=[
            ('approval', 'Approval'),
            ('reject', 'Reject'),
            ('cancel', 'Cancel'),
        ],
        required=False, )

    def x_request_approval_action(self):
        print('request approval form')

    def x_decision_action(self):
        print('request approval form')

    @api.constrains("x_deadline")
    def _check_x_deadline(self):
        for r in self:
            if r.request_deadline < fields.Datetime.now():
                raise ValidationError(_("You can not set a deadline which is in the past!"))

    def x_request(self):
        if not self.user_has_groups("sales_team.group_sale_salesman"):
            raise ValidationError(_("You are not permitted to request approval for sale quotation!"))
        self.ensure_one()

        self.sale_order_id.sudo().write({
            "x_deadline": self.x_deadline,
        })
        # self.sale_order_id.request_approval(self.x_comment)