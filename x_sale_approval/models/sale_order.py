# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "x.x_company_organization.org_mixin"]

    # Approval
    approver_id = fields.Many2one("res.users", string="申請先", readonly=True)
    x_deadline = fields.Date(string='承認希望日', required=False, default=fields.Date.today() + timedelta(days=7))
    x_remark = fields.Char(string='備考', required=False)
    x_reason = fields.Char(string='理由', required=False)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('approval_requested', '承認申請済'),
        ('rejected', '否認済'),
        ('remand', '差し戻し'),
        ('approved', '承認済'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    x_state = fields.Selection(
        string='判断',
        selection=[
            ('rejected', '否認'),
            ('approved', '承認'),
            ('remand', '差し戻し'),
        ],
        required=False, )

    active = fields.Boolean(
        string="Active", default=True
    )

    def action_request_quotation_approval(self):
        return {
            'name': _("Quotation Request"),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.quotation.approval.request.wizard',
            'target': 'new'
        }

    def action_approve_quotation(self):
        return {
            'name': _("Quotation Approve"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.quotation.approve.wizard',
            'target': 'new',
            'type': 'ir.actions.act_window'
        }

    def write(self, vals):
        if vals.get('order_line'):
            for order in self:
                for order_line in order.order_line:
                    if order_line.x_expected_delivery_date < fields.Date.today():
                        raise ValidationError(_("納期は現在より過去の日付は設定できません"))
        return super(SaleOrder, self).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('order_line'):
            for order in self:
                for order_line in order.order_line:
                    if order_line.x_expected_delivery_date < fields.Date.today():
                        raise ValidationError(_("納期は現在より過去の日付は設定できません"))
        return super(SaleOrder, self).create(vals)

    @api.depends('x_state')
    def _depends_x_state(self):
        # TODO: sending email or notification when user change state
        pass

