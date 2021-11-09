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
    x_reject = fields.Char('Reason for rejection')
    x_transfer_date = fields.Date('Remittance date')
    x_is_multiple_approval = fields.Boolean(related='category_id.x_is_multiple_approval')
    multi_approvers_ids = fields.One2many(
        'ss_erp.multi.approvers', 'x_request_id', string='Multi-step approval', readonly=True, copy=False)
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

    def _pass_multi_approvers(self):
        curren_multi_approvers = self.multi_approvers_ids.filtered(lambda p: p.is_current)
        no_curren_multi_approvers = self.multi_approvers_ids.filtered(
            lambda p: not p.is_current and p.x_user_status == 'new')
        if no_curren_multi_approvers:
            no_curren_multi_approvers[0].write({'is_current': True})
        if curren_multi_approvers:
            curren_multi_approvers[0].write({'is_current': False})
        if self.request_status != 'approved' and no_curren_multi_approvers:
            self._genera_approver_ids(no_curren_multi_approvers[0])

    @api.onchange('category_id', 'request_owner_id')
    def _onchange_category_id(self):
        if self.category_id.x_is_multiple_approval:
            cate_approvers_ids = self.category_id.multi_approvers_ids
            current_users = self.approver_ids.mapped('user_id')
            new_users = cate_approvers_ids.mapped('x_approver_group_ids')
            multi_approvers_ids = self.env['ss_erp.multi.approvers']

            for multi_approvers_id in cate_approvers_ids:
                new_vals = {
                    'x_request_id': self.id,
                    'x_approval_seq': multi_approvers_id.x_approval_seq,
                    'x_user_status': 'new',
                    'x_approver_group_ids': [(6, 0, multi_approvers_id.x_approver_group_ids.ids)] if multi_approvers_id.x_approver_group_ids else False,
                    'x_related_user_ids': [(6, 0, multi_approvers_id.x_related_user_ids.ids)] if multi_approvers_id.x_related_user_ids else False,
                    'x_is_manager_approver': multi_approvers_id.x_is_manager_approver,
                    'x_minimum_approvers': multi_approvers_id.x_minimum_approvers,
                }
                multi_approvers_ids += self.env['ss_erp.multi.approvers'].new(new_vals)
            if multi_approvers_ids:
                multi_approvers_ids[0].is_current = True
            self.multi_approvers_ids = multi_approvers_ids

        else:
            super(ApprovalRequest, self)._onchange_category_id()

    def _genera_approver_ids(self, multi_approvers):
        current_users = self.approver_ids.mapped('user_id')
        new_users = multi_approvers.x_approver_group_ids

        if multi_approvers.x_is_manager_approver:
            employee = self.env['hr.employee'].search(
                [('user_id', '=', self.request_owner_id.id)], limit=1)
            if employee.parent_id.user_id:
                new_users |= employee.parent_id.user_id

        self.write({
            'approver_ids': [(5, 0, 0)] + [(0, 0, {
                'user_id': user.id,
                'request_id': self.id,
                'status': 'pending'
            }) for user in new_users]
        })

    def _check_user_access_request(self):
        if self.category_id.x_is_multiple_approval:
            curren_multi_approvers = self.multi_approvers_ids.filtered(lambda p: p.is_current)
            if curren_multi_approvers:
                access_user_ids = curren_multi_approvers[0].mapped('x_approver_group_ids')
                if curren_multi_approvers[0].x_is_manager_approver:
                    employee = self.env['hr.employee'].search(
                        [('user_id', '=', self.request_owner_id.id)], limit=1)
                    if employee.parent_id.user_id:
                        access_user_ids |= employee.parent_id.user_id
                if self.env.user not in access_user_ids:
                    return False
        return True

    # Override
    # 'approval_minimum' use to check 'multi_approvers_ids'
    def action_confirm(self):
        if self.request_owner_id != self.env.user:
            raise UserError(_("Only the applicant can submit."))
        # if len(self.multi_approvers_ids) < self.approval_minimum:
        #     raise UserError(
        #         _("You have to add at least %s multi-step approvers to confirm your request.", self.approval_minimum))
        if self.requirer_document == 'required' and not self.attachment_number:
            raise UserError(_("You have to attach at lease one document."))

        if self.category_id.x_is_multiple_approval:
            curren_multi_approvers = self.multi_approvers_ids.filtered(lambda p: p.is_current)
            if curren_multi_approvers:
                self._genera_approver_ids(curren_multi_approvers[0])
        # super(ApprovalRequest, self).action_confirm()
        #
        approvers = self.mapped('approver_ids').filtered(lambda approver: approver.status == 'new')
        approvers._create_activity()
        approvers.write({'status': 'pending'})
        self.write({'date_confirmed': fields.Datetime.now()})

        # if self.category_id.x_is_multiple_approval:
        #     self.mapped('multi_approvers_ids').write({'x_user_status': 'pending'})
        if self.x_contact_form_id:
            self.x_contact_form_id.write(
                {'approval_id': self.id, 'approval_state': self.request_status})

    def _approve_multi_approvers(self, user):
        curren_multi_approvers = self.multi_approvers_ids.filtered(lambda p: p.is_current)
        if curren_multi_approvers:
            curren_multi_approvers[0].write({'x_existing_request_user_ids': [(4, user.id)]})

    def action_approve(self, approver=None):
        if self.category_id.x_is_multiple_approval:
            if not self._check_user_access_request():
                raise UserError(_("We cannot approve this application."))
        super(ApprovalRequest, self).action_approve(approver=approver)
        if self.category_id.x_is_multiple_approval:
            self._approve_multi_approvers(self.env.user)

    def _refuse_multi_approvers(self):
        curren_multi_approvers = self.multi_approvers_ids.filtered(lambda p: p.is_current)
        if curren_multi_approvers:
            curren_multi_approvers[0].write({'x_user_status': 'refused'})

    def action_refuse(self, approver=None):
        if self.category_id.x_is_multiple_approval:
            if not self._check_user_access_request():
                raise UserError(_("We cannot refuse this application."))
        super(ApprovalRequest, self).action_refuse(approver=approver)
        if self.category_id.x_is_multiple_approval:
            self._refuse_multi_approvers()

    def _withdraw_multi_approvers(self, user):
        curren_multi_approvers = self.multi_approvers_ids.filtered(lambda p: p.is_current)
        if curren_multi_approvers:
            if user in curren_multi_approvers[0].x_existing_request_user_ids:
                curren_multi_approvers[0].write({'x_existing_request_user_ids': [(3, user.id)]})
            if curren_multi_approvers[0].x_user_status == 'refused':
                curren_multi_approvers[0].write({'x_user_status': 'pending'})

    def action_withdraw(self, approver=None):
        super(ApprovalRequest, self).action_withdraw(approver=approver)
        if self.category_id.x_is_multiple_approval:
            self._withdraw_multi_approvers(self.env.user)

    def action_draft(self):
        if self.request_owner_id != self.env.user:
            raise UserError(_("Only the applicant can back to draft."))
        super(ApprovalRequest, self).action_draft()
        if self.category_id.x_is_multiple_approval:
            self.mapped('multi_approvers_ids').write({'x_user_status': 'new'})
            # Clear flag
            self.multi_approvers_ids.write({'is_current': False})
            # Update flag
            self.multi_approvers_ids[0].write({'is_current': True})

    def _cancel_multi_approvers(self):
        curren_multi_approvers = self.multi_approvers_ids.filtered(lambda p: p.is_current)
        if curren_multi_approvers:
            curren_multi_approvers[0].write({'x_user_status': 'cancel'})
        self.multi_approvers_ids.write({'x_existing_request_user_ids': [(5, 0, 0)]})

    def action_cancel(self):
        # self.sudo()._get_user_approval_activities(user=self.env.user).unlink()
        if self.request_owner_id != self.env.user:
            raise UserError(_("Only the applicant can cancel."))
        super(ApprovalRequest, self).action_cancel()
        if self.category_id.x_is_multiple_approval:
            self._cancel_multi_approvers()

    # Override : compute with multi_approvers_ids
    # old_version : compute with approver_ids
    @api.depends('multi_approvers_ids.x_user_status')
    def _compute_request_status(self):
        for request in self:
            status_lst = request.mapped('multi_approvers_ids.x_user_status')
            status_lst_pp = request.mapped('approver_ids.status')
            minimal_approver = request.approval_minimum if len(
                status_lst) >= request.approval_minimum else len(status_lst)
            if status_lst:
                if status_lst.count('cancel'):
                    status = 'cancel'
                elif status_lst.count('refused'):
                    status = 'refused'
                elif status_lst.count('new') and (status_lst_pp.count('new') or not request.approver_ids):
                    status = 'new'
                # elif status_lst.count('approved') >= minimal_approver:
                elif status_lst.count('approved') >= len(status_lst):
                    status = 'approved'
                else:
                    status = 'pending'
            else:
                status = 'new'
            request.request_status = status
            request.x_contact_form_id.write({'approval_state': request.request_status})
