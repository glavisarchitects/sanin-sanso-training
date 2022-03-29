# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    x_department_id = fields.Many2one(
        'ss_erp.responsible.department', string='申請部署', )
    x_organization_id = fields.Many2one(
        'ss_erp.organization', string='申請組織')
    x_contact_form_id = fields.Many2one(
        'ss_erp.res.partner.form', string='連絡先申請フォーム')
    x_inventory_order_ids = fields.Many2many(
        'stock.inventory', 'inventory_request_rel', 'inventory_id', 'request_id', string='棚卸伝票')
    x_sale_order_ids = fields.Many2many(
        'sale.order', 'sale_order_request_rel', 'sale_id', 'request_id', string='見積伝票')
    x_account_move_ids = fields.Many2many(
        'account.move', 'account_move_request_rel', 'move_id', 'request_id', string='仕入請求伝票')
    x_purchase_order_ids = fields.Many2many(
        'purchase.order', 'purchase_request_rel', 'purchase_id', 'request_id', string='見積依頼伝票')
    x_payment_date = fields.Date('請求書締日')
    x_purchase_material = fields.Text('仕入商材')
    x_cash_amount = fields.Float('現金仕入額')
    x_cash_payment_date = fields.Date('現金支払日')
    x_prepay_amount = fields.Float('前払仕入額')
    x_prepay_payment_date = fields.Date('前払支払日')
    x_payment_reason = fields.Text('支払理由')
    x_transfer_preferred_date = fields.Date('送金希望日')
    x_present_date = fields.Date('残高現在日')
    x_cash_balance = fields.Float('現金残高')
    x_bank_balance = fields.Float('預金残高')
    x_reject = fields.Char('却下理由')
    x_transfer_date = fields.Date('送金日')
    x_is_multiple_approval = fields.Boolean(related='category_id.x_is_multiple_approval')
    multi_approvers_ids = fields.One2many(
        'ss_erp.multi.approvers', 'x_request_id', string='多段階承認', readonly=True, copy=False)
    x_inventory_instruction_ids = fields.Many2many(
        'ss_erp.instruction.order', 'instruction_request_rel', 'instruction_id', 'request_id',
        string='指示伝票')

    x_approval_date = fields.Date('申請日', default=datetime.now())

    last_approver = fields.Many2one('res.users', string='最終承認者')
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
    has_x_inventory_instruction_ids = fields.Selection(
        related='category_id.has_x_inventory_instruction_ids', store=True)

    hide_btn_cancel = fields.Boolean(compute='_compute_hide_btn_cancel')
    show_btn_temporary_approve = fields.Boolean(compute='_compute_show_btn_temporary_approve')
    show_btn_approve = fields.Boolean(compute='_compute_show_btn_approve')
    show_btn_draft = fields.Boolean(compute='_compute_show_btn_draft')
    show_btn_refuse = fields.Boolean(compute='_compute_show_btn_refuse')

    def _compute_show_btn_draft(self):
        for request in self:
            request.show_btn_draft = True if request.request_owner_id == self.env.user and request.request_status in [
                'refused', 'cancel'] else False

    def _compute_hide_btn_cancel(self):
        for request in self:
            request.hide_btn_cancel = False if request.request_owner_id == self.env.user and request.request_status == 'pending' else True

    def _compute_show_btn_temporary_approve(self):
        for request in self:
            index_user = request._get_index_user_multi_approvers()
            request.show_btn_temporary_approve = True if index_user and index_user > 0 and \
                                                         request.user_status and request.user_status == 'pending' and \
                                                         request.multi_approvers_ids[
                                                             index_user - 1].x_user_status != 'approved' and request.request_status == 'pending' \
                else False

    def _compute_show_btn_refuse(self):
        for request in self:
            request.show_btn_refuse = False
            if request.category_id.x_is_multiple_approval:
                if request.request_status == 'pending':
                    index = 0
                    while index < len(self.multi_approvers_ids):
                        if self.multi_approvers_ids[index].x_user_status in ['new', 'pending']:
                            if self.env.user in self.multi_approvers_ids[index].x_approver_group_ids:
                                current_user_status = self.env['approval.approver'].search(
                                    [('request_id', '=', request.id), ('user_id', '=', self.env.user.id)], limit=1)
                                if current_user_status and current_user_status.status in ['new', 'pending']:
                                    request.show_btn_refuse = True
                                    break
                        index += 1
            else:
                if request.request_status == 'pending':
                    if self.env.user in request.category_id.user_ids:
                        request.show_btn_refuse = True

    def _compute_show_btn_approve(self):
        for request in self:
            # ('user_status','!=','pending')
            index_user = request._get_index_user_multi_approvers()
            if request.request_status not in ['cancel', 'refuse'] and request.user_status == 'pending' and (
                    not index_user or (index_user > 0 and
                                       request.multi_approvers_ids[
                                           index_user - 1].x_user_status == 'approved')):
                request.show_btn_approve = True
            else:
                request.show_btn_approve = False

    @api.onchange('category_id', 'request_owner_id')
    def _onchange_category_id(self):
        if self.x_is_multiple_approval:
            cate_approvers_ids = self.category_id.multi_approvers_ids
            multi_approvers_ids = self.env['ss_erp.multi.approvers']
            seq = 0
            for multi_approvers_id in cate_approvers_ids:
                seq += 1
                x_approver_ids = multi_approvers_id.x_approver_group_ids.ids if multi_approvers_id.x_approver_group_ids else []
                if multi_approvers_id.x_is_manager_approver:
                    employee = self.env['hr.employee'].search(
                        [('user_id', '=', self.env.user.id)], limit=1)
                    if employee.parent_id.user_id:
                        x_approver_ids.append(employee.parent_id.user_id.id)

                x_approver_group_ids = [(6, 0, x_approver_ids)]
                new_vals = {
                    'x_request_id': self.id,
                    'x_approval_seq': seq,
                    'x_user_status': 'new',
                    'x_approver_group_ids': x_approver_group_ids,
                    'x_related_user_ids': [(6, 0,
                                            multi_approvers_id.x_related_user_ids.ids)] if multi_approvers_id.x_related_user_ids else False,
                    'x_is_manager_approver': multi_approvers_id.x_is_manager_approver,
                    'x_minimum_approvers': multi_approvers_id.x_minimum_approvers,
                }
                if len(x_approver_ids) > 0:
                    multi_approvers_ids += self.env['ss_erp.multi.approvers'].new(new_vals)
            self.multi_approvers_ids = multi_approvers_ids
        else:
            super(ApprovalRequest, self)._onchange_category_id()

    def _genera_approver_ids(self):
        new_users = list(set(self.multi_approvers_ids.mapped('x_approver_group_ids')))

        self.write({
            'approver_ids': [(5, 0, 0)] + [(0, 0, {
                'user_id': user.id,
                'request_id': self.id,
                'status': 'new'
            }) for user in new_users]
        })

    def notify_approval(self, users, approver=None):
        # message_subscribe

        partner_ids = users.mapped('partner_id').ids
        body_template = self.env.ref('ss_erp.message_multi_approver_assigned')
        self = self.with_context(lang=self.env.user.lang)
        body_template = body_template.with_context(lang=self.env.user.lang)
        model_description = self.env['ir.model']._get('approval.request').display_name
        if self.request_status == 'approved' and self.x_contact_form_id and self.x_contact_form_id.res_partner_id:
            partner = self.env['res.partner'].browse(int(self.x_contact_form_id.res_partner_id))
        else:
            partner = False
        body = body_template._render(
            dict(
                request=self,
                model_description=model_description,
                approver=approver,
                approver_date=fields.Date.context_today(self),
                reject_date=fields.Date.context_today(self),
                partner=partner,
                access_link=self.env['mail.thread']._notify_get_action_link(
                    'view', model=self._name, res_id=self.id),
            ),
            engine='ir.qweb',
            minimal_qcontext=True
        )
        subject = _('%(name)s: %(summary)s assigned to you',
                    name=self.name, summary=self._description)
        if approver and self.request_status != 'approved':
            subject = _('%(name)s: %(summary)s is approve by %(approver)s',
                        name=self.name, summary=self._description, approver=approver.name)

        if approver and self.request_status == 'approved':
            subject = _('%(name)s: %(summary)s is approved',
                        name=self.name, summary=self._description)
        if self.request_status == 'refused':
            subject = _('%(name)s: %(summary)s is rejected',
                        name=self.name, summary=self._description)

        self.message_notify(
            partner_ids=partner_ids,
            body=body,
            subject=subject,
            record_name=self.name,
            model_description=model_description,
            email_layout_xmlid='mail.mail_notification_light',
        )

    # Override
    def action_confirm(self):
        if not self.x_is_multiple_approval and len(self.approver_ids) < self.approval_minimum:
            raise UserError(
                _("You have to add at least %s approvers to confirm your request.", self.approval_minimum))
        if self.request_owner_id != self.env.user:
            raise UserError(_("Only the applicant can submit."))
        if self.requirer_document == 'required' and not self.attachment_number:
            raise UserError(_("You have to attach at lease one document."))
        self.write({'date_confirmed': fields.Datetime.now()})

        if self.x_is_multiple_approval:
            self._genera_approver_ids()
            self.multi_approvers_ids.write({'x_user_status': 'pending'})

        approvers = self.mapped('approver_ids').filtered(lambda approver: approver.status == 'new')
        approvers.write({'status': 'pending'})

        if self.request_owner_id.id in self.mapped('approver_ids.user_id').ids:
            self.action_approve(approver=self.request_owner_id.id)

        if self.x_is_multiple_approval:
            if self.multi_approvers_ids.filtered(lambda x: x.x_user_status == 'pending'):
                first_group_user_ids = self.multi_approvers_ids.filtered(lambda x: x.x_user_status == 'pending')[
                    0].x_approver_group_ids.ids
                create_activity_approvers = approvers.filtered(lambda x: x.user_id.id in first_group_user_ids)
                create_activity_approvers._create_activity()
        else:
            approvers.filtered(lambda x: x.status == 'pending')._create_activity()

        if self.category_id.approval_type in ['inventory_request', 'inventory_request_manager']:
            if self.x_inventory_order_ids:
                self.x_inventory_order_ids.write({
                    'state': 'approval'
                })
            if self.x_inventory_instruction_ids:
                self.x_inventory_instruction_ids.write({
                    'state': 'approval'
                })

        if self.x_contact_form_id:
            self.x_contact_form_id.write(
                {'approval_id': self.id, 'approval_state': self.request_status})

        user = self.multi_approvers_ids.mapped('x_related_user_ids')
        self.notify_approval(users=user)

    def _approve_multi_approvers(self, user):
        curren_multi_approvers = self.multi_approvers_ids.filtered(
            lambda p: user in p.x_approver_group_ids)
        if curren_multi_approvers:
            curren_multi_approvers.write({'x_existing_request_user_ids': [(4, user.id)]})
            users = curren_multi_approvers.mapped('x_approver_group_ids') - self.env.user
            self.notify_approval(users=users, approver=self.env.user)
            current_approved_number = self.approver_ids.filtered(
                lambda x: x.status == 'approved' and x.user_id in curren_multi_approvers.mapped('x_approver_group_ids'))
            if len(current_approved_number) >= curren_multi_approvers.x_minimum_approvers:
                curren_multi_approvers.write({'x_user_status': 'approved'})

            if curren_multi_approvers.x_user_status == 'approved':
                next_multi_approvers = self.multi_approvers_ids.filtered(
                    lambda p: p.x_approval_seq == curren_multi_approvers.x_approval_seq + 1)
                if next_multi_approvers:
                    users = next_multi_approvers.mapped('x_approver_group_ids') - self.env.user
                    self.notify_approval(users=users, approver=self.env.user)

    def action_approve(self, approver=None):
        super(ApprovalRequest, self).action_approve(approver=approver)
        if self.x_is_multiple_approval:
            self._approve_multi_approvers(self.env.user)
        self.sudo().write({'last_approver': self.env.user.id})

    def _refuse_multi_approvers(self):
        curren_multi_approvers = self.multi_approvers_ids.filtered(
            lambda p: self.env.user in p.x_approver_group_ids)
        if curren_multi_approvers:
            curren_multi_approvers.write({'x_user_status': 'refused'})

    def action_refuse(self, approver=None, lost_reason=None):
        super(ApprovalRequest, self).action_refuse(approver=approver)
        if self.x_is_multiple_approval:
            self._refuse_multi_approvers()

        users = self.request_owner_id
        users |= self.multi_approvers_ids.mapped('x_related_user_ids')
        self.notify_approval(users=users, approver=self.env.user)
        self.sudo().write({'last_approver': self.env.user.id})
        self.activity_ids.sudo().unlink()

    def action_draft(self):
        if self.request_owner_id != self.env.user:
            raise UserError(_("Only the applicant can back to draft."))
        super(ApprovalRequest, self).action_draft()
        if self.x_is_multiple_approval:
            self.multi_approvers_ids.write({'x_user_status': 'new'})
        self.activity_ids.sudo().unlink()

    def _cancel_multi_approvers(self):
        self.multi_approvers_ids.write(
            {'x_existing_request_user_ids': [(5, 0, 0)], 'x_user_status': 'cancel'})
        self.activity_ids.sudo().unlink()

    def action_cancel(self):
        self.sudo()._get_user_approval_activities(user=self.env.user).unlink()
        super(ApprovalRequest, self).action_cancel()
        if self.x_is_multiple_approval:
            self._cancel_multi_approvers()

    def _get_index_user_multi_approvers(self):
        index_current = None
        for index in range(len(self.multi_approvers_ids)):
            if self.env.user in self.multi_approvers_ids[index].x_approver_group_ids:
                index_current = index
        return index_current

    def action_temporary_approve(self):
        if self.x_is_multiple_approval:
            # if not self._check_user_access_request():
            #     raise UserError(_("We cannot approve this request."))
            self.action_approve()
            index_current = self._get_index_user_multi_approvers()
            if index_current and index_current > 0:
                for index in range(index_current):
                    multi_approvers_id = self.multi_approvers_ids[index]
                    all_users = multi_approvers_id.x_approver_group_ids
                    if multi_approvers_id.x_is_manager_approver:
                        employee = self.env['hr.employee'].search(
                            [('user_id', '=', self.request_owner_id.id)], limit=1)
                        if employee.parent_id.user_id:
                            all_users |= employee.parent_id.user_id
                    if all_users:
                        self.mapped('approver_ids').filtered(
                            lambda approver: approver.user_id in all_users
                        ).write({'status': 'approved'})
                        multi_approvers_id.write(
                            {'x_existing_request_user_ids': [(6, 0, all_users.ids)]})

    # Override
    @api.depends('x_is_multiple_approval', 'multi_approvers_ids.x_user_status', 'approver_ids.status')
    def _compute_request_status(self):
        for request in self:
            if request.x_is_multiple_approval:
                status_lst = request.mapped('multi_approvers_ids.x_user_status')
                status_lst_pp = request.mapped('approver_ids.status')
                if status_lst:
                    if status_lst.count('cancel'):
                        status = 'cancel'
                    elif status_lst.count('refused'):
                        status = 'refused'
                    elif status_lst.count('new') and (status_lst_pp.count('new') or not request.approver_ids):
                        status = 'new'
                    elif status_lst.count('approved') >= len(status_lst):
                        status = 'approved'
                    else:
                        status = 'pending'
                else:
                    status = 'new'

            else:
                status_lst = request.mapped('approver_ids.status')
                minimal_approver = request.approval_minimum if len(
                    status_lst) >= request.approval_minimum else len(status_lst)
                if status_lst:
                    if status_lst.count('cancel'):
                        status = 'cancel'
                    elif status_lst.count('refused'):
                        status = 'refused'
                    elif status_lst.count('new'):
                        status = 'new'
                    elif status_lst.count('approved') >= minimal_approver:
                        status = 'approved'
                    else:
                        status = 'pending'
                else:
                    status = 'new'

            request.request_status = status

            # 仕入先フォーム更新
            if request.x_contact_form_id:
                request.x_contact_form_id.sudo().write({'approval_state': request.request_status})

            # 見積・受注更新
            if request.x_sale_order_ids:
                for so in request.x_sale_order_ids:
                    if status == 'approved':
                        so.sudo().write({'approval_status': 'approved'})
                    elif status == 'pending':
                        so.sudo().write({'approval_status': 'in_process'})

            # 棚卸更新
            if request.request_status == 'approved':
                if request.category_id.approval_type in ['inventory_request', 'inventory_request_manager']:
                    if request.x_inventory_order_ids:
                        request.x_inventory_order_ids.write({
                            'state': 'done'
                        })
                        request.x_inventory_order_ids.mapped('instruction_order_id').write({
                            'state': 'waiting'
                        })
                    if request.x_inventory_instruction_ids:
                        request.x_inventory_instruction_ids.write({
                            'state': 'approved'
                        })

                users = request.multi_approvers_ids.mapped('x_related_user_ids')
                users |= request.request_owner_id
                self.notify_approval(users=users, approver=request.last_approver)
