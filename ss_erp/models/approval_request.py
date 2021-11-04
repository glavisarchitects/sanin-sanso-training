# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    x_department_id = fields.Many2one(
        'hr.employee', string='Application department')
    x_organization_id = fields.Many2one(
        'ss_erp.organization', string='Application organization')
    x_contact_form_id = fields.Many2one(
        'ss_erp.res.partner.form', string='Contact application form')
    x_inventory_order_ids = fields.Many2many(
        'stock.inventory', 'inventory_request_rel', 'inventory_id', 'request_id', string='Inventory slip')
    x_sale_order_ids = fields.Many2many(
        'sale.order', 'sale_order_request_rel', 'sale_id', 'request_id', string='Quotation slip')
    x_account_move_ids = fields.Many2many(
        'account.move', 'account_move_request_rel', 'move_id', 'request_id', string='Purchase request slip')
    x_purchase_order_ids = fields.Many2many(
        'purchase.order', 'purchase_request_rel', 'purchase_id', 'request_id', string='Quotation request slip')
    x_payment_date = fields.Date('Invoice closing date')
    x_purchase_material = fields.Text('Purchased products')
    x_cash_amount = fields.Float('Cash purchase amount')
    x_cash_payment_date = fields.Date('Cash payment date')
    x_prepay_amount = fields.Float('Prepaid purchase amount')
    x_prepay_payment_date = fields.Date('Prepaid payment date')
    x_payment_reason = fields.Text('Reason for payment')
    x_transfer_preferred_date = fields.Date('Desired remittance date')
    x_present_date = fields.Date('Balance current date')
    x_cash_balance = fields.Float('Cash balance')
    x_bank_balance = fields.Float('Deposit balance')
    x_transfer_date = fields.Date('Remittance date')
    x_is_multiple_approval = fields.Boolean(related='category_id.x_is_multiple_approval')
    multi_approvers_ids = fields.One2many(
        'ss_erp.multi.approvers', 'x_request_id', string='Multi-step approval')
    # FIELD RELATED
    has_x_organization = fields.Selection(
        related='category_id.has_x_organization', store=True)
    has_x_department = fields.Selection(
        related='category_id.has_x_department', store=True)
    has_x_reject = fields.Selection(
        related='category_id.has_x_reject', store=True)
    has_x_contact_form_id = fields.Selection(
        related='category_id.has_x_contact_form_id', store=True)
    has_x_inventory_order_ids = fields.Selection(
        related='category_id.has_x_inventory_order_ids', store=True)
    has_x_sale_order_ids = fields.Selection(
        related='category_id.has_x_sale_order_ids', store=True)
    has_x_account_move_ids = fields.Selection(
        related='category_id.has_x_account_move_ids', store=True)
    has_x_payment_date = fields.Selection(
        related='category_id.has_x_payment_date', store=True)
    has_x_purchase_material = fields.Selection(
        related='category_id.has_x_purchase_material', store=True)
    has_x_cash_amount = fields.Selection(
        related='category_id.has_x_cash_amount', store=True)
    has_x_cash_payment_date = fields.Selection(
        related='category_id.has_x_cash_payment_date', store=True)
    has_x_prepay_amount = fields.Selection(
        related='category_id.has_x_prepay_amount', store=True)
    has_x_prepay_payment_date = fields.Selection(
        related='category_id.has_x_prepay_payment_date', store=True)
    has_x_payment_reason = fields.Selection(
        related='category_id.has_x_payment_reason', store=True)
    has_x_purchase_order_ids = fields.Selection(
        related='category_id.has_x_purchase_order_ids', store=True)
    has_x_transfer_preferred_date = fields.Selection(
        related='category_id.has_x_transfer_preferred_date', store=True)
    has_x_present_date = fields.Selection(
        related='category_id.has_x_present_date', store=True)
    has_x_cash_balance = fields.Selection(
        related='category_id.has_x_cash_balance', store=True)
    has_x_bank_balance = fields.Selection(
        related='category_id.has_x_bank_balance', store=True)
    has_x_transfer_date = fields.Selection(
        related='category_id.has_x_transfer_date', store=True)

    def action_confirm(self):
        super(ApprovalRequest, self).action_confirm()
        if self.x_contact_form_id:
            # TODO: fix here
            self.x_contact_form_id.write({'approval_id': self.id, 'approval_state': self.request_status})

    @api.onchange('category_id', 'request_owner_id')
    def _onchange_category_id(self):
        if self.category_id.x_is_multiple_approval:
            cate_approvers_ids = self.category_id.multi_approvers_ids
            current_users = self.approver_ids.mapped('user_id')
            new_users = cate_approvers_ids.mapped('x_approver_group_ids')
            multi_approvers_ids = self.env['ss_erp.multi.approvers']

            for multi_approvers_id in cate_approvers_ids:
                multi_approvers_ids += self.env['ss_erp.multi.approvers'].new({
                    'x_request_id': self.id,
                    'x_user_status': 'new',
                    'x_approver_group_ids': [(6, 0, multi_approvers_id.x_approver_group_ids.ids)] if multi_approvers_id.x_approver_group_ids else False,
                    'x_related_user_ids': [(6, 0, multi_approvers_id.x_related_user_ids.ids)] if multi_approvers_id.x_related_user_ids else False,
                    'x_is_manager_approver': multi_approvers_id.x_is_manager_approver,
                    'x_minimum_approvers': multi_approvers_id.x_minimum_approvers,
                })
                if multi_approvers_id.x_is_manager_approver:
                    employee = self.env['hr.employee'].search([('user_id', '=', self.request_owner_id.id)], limit=1)
                    if employee.parent_id.user_id:
                        new_users |= employee.parent_id.user_id

            self.multi_approvers_ids = multi_approvers_ids

            for user in new_users - current_users:
                self.approver_ids += self.env['approval.approver'].new({
                    'user_id': user.id,
                    'request_id': self.id,
                    'status': 'new'
                })

        else:
            super(ApprovalRequest, self)._onchange_category_id()

    @api.depends('approver_ids.status')
    def _compute_request_status(self):
        super(ApprovalRequest, self)._compute_request_status()
        for request in self:
            # if request.request_status == 'cancel':
            #     status = _("Cancel")
            # elif request.request_status == 'refused':
            #     status = _("Rejected")
            # elif request.request_status == 'approved':
            #     status = _("Approved")
            #     request.action_process_with_contact_form()
            # elif request.request_status == 'pending':
            #     status = _("Unapproved")
            # else:
            #     status = _("New")
            request.x_contact_form_id.write({'approval_state': request.request_status})
