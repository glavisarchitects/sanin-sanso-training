# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class SaleQuotationApprovalRequestWizard(models.TransientModel):
    _name = 'sale.quotation.approval.request.wizard'

    approver_id = fields.Many2one("res.users", string="申請先", required=True)
    x_deadline = fields.Date(string='承認希望日', required=False, default=fields.Date.today() + timedelta(days=7))
    x_remark = fields.Char(string='備考', required=False, help='comment')

    @api.constrains("x_deadline")
    def _check_x_deadline(self):
        for r in self:
            if r.x_deadline < fields.Date.today():
                # Message = You can not set a deadline which is in the past!
                raise ValidationError(_("申請期日は本日よりも後にしてください"))

    def action_request(self):
        sale_order = self.env['sale.order'].browse(self.env.context.get('active_ids'))

        sale_order.write({
            'state': 'approval_requested',
            'x_deadline': self.x_deadline,
            'approver_id': self.approver_id,
            'x_remark': self.x_remark
        })


class SaleQuotationApproveWizard(models.TransientModel):
    _name = 'sale.quotation.approve.wizard'

    x_reason = fields.Char(string='理由', required=False, help='reason')

    x_state = fields.Selection(
        string='判断',
        selection=[
            ('rejected', '否認'),
            ('approved', '承認'),
            ('remand', '差し戻し'),
        ],
        required=False, )

    def action_approve(self):
        if not self.x_state:
            raise ValidationError(_("「承認」「否認」「差し戻し」のいずれかを選択してください"))
        if self.x_state in ['rejected', 'remand'] and not self.x_reason:
            raise ValidationError(_("「否認」「差し戻し」の場合は、理由を入力してください"))

        sale_order = self.env['sale.order'].browse(self.env.context.get('active_ids'))

        sale_order.write({
            'state': self.x_state,
            'x_state': self.x_state,
            'x_reason': self.x_reason
        })
