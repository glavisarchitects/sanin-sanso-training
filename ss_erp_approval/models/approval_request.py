# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    x_department_id = fields.Many2one(
        'ss_erp.responsible.department', string='申請部署',
        default=lambda self: self._get_default_x_responsible_dept_id())

    x_organization_id = fields.Many2one('ss_erp.organization', string='申請組織', default=lambda self: self._get_default_x_organization_id())

    def _get_default_x_organization_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id.organization_first
        else:
            return False

    def _get_default_x_responsible_dept_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id and employee_id.department_jurisdiction_first:
            return employee_id.department_jurisdiction_first[0]
        else:
            return False

    x_contact_form_id = fields.Many2one(
        'ss_erp.res.partner.form', string='連絡先申請フォーム')
    x_product_template_form_id = fields.Many2one(
        'ss_erp.product.template.form', string='プロダクト申請フォーム')
    x_inventory_order_ids = fields.Many2many(
        'stock.inventory', 'inventory_request_rel', 'inventory_id', 'request_id', string='棚卸伝票')
    x_sale_order_ids = fields.Many2many(
        'sale.order', 'ss_erp_sale_order_request_rel', 'sale_id', 'request_id', string='見積伝票')
    x_lpgas_inventory_ids = fields.Many2many('ss_erp.lpgas.order', string='LPガス棚卸伝票')
    x_account_move_ids = fields.Many2many(
        'account.move', 'ss_erp_account_move_request_rel', 'move_id', 'request_id', string='仕入請求伝票')
    x_purchase_order_ids = fields.Many2many(
        'purchase.order', 'ss_erp_purchase_request_rel', 'purchase_id', 'request_id', string='見積依頼伝票')
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
        'ss_erp.instruction.order', 'ss_erp_instruction_request_rel', 'instruction_id', 'request_id',
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
    has_x_product_template_form_id = fields.Selection(
        related='category_id.has_x_product_template_form_id', store=True)
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
    has_lp_gas_inventory_ids = fields.Selection(
        related='category_id.has_lp_gas_inventory_ids', store=True)

    x_current_sequence = fields.Integer(compute='_compute_current_sequence', store=True)
    x_user_sequence = fields.Integer(compute='_compute_current_sequence')

    def _get_default_x_organization_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id.organization_first
        else:
            return False

    def _get_default_x_responsible_dept_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id and employee_id.department_jurisdiction_first:
            return employee_id.department_jurisdiction_first[0]
        else:
            return False
    def _compute_current_sequence(self):
        for rec in self:
            rec.x_current_sequence = False
            if rec.request_status == 'pending':
                set_approvers = set(rec.multi_approvers_ids.filtered(lambda r: r.x_user_status == 'pending').mapped(
                    'x_approval_seq'))
                rec.x_current_sequence = min(set_approvers) if set_approvers else 0
            rec.x_user_sequence = rec.multi_approvers_ids.filtered(
                lambda r: self.env.user in r.x_approval_user_ids).x_approval_seq

    @api.constrains('x_approval_date')
    def _check_x_approval_date(self):
        for request in self:
            if request.x_approval_date < datetime.today().date():
                raise UserError('申請期日が現在日付より過去日になっています。')

    show_btn_temporary_approve = fields.Boolean(compute='_compute_show_btn_temporary_approve')
    show_btn_approve = fields.Boolean(compute='_compute_show_btn_approve')
    show_btn_draft = fields.Boolean(compute='_compute_show_btn_draft')
    show_btn_refuse = fields.Boolean(compute='_compute_show_btn_refuse')

    def _compute_show_btn_draft(self):
        for request in self:
            request.show_btn_draft = True if request.request_owner_id == self.env.user and request.request_status in [
                'refused', 'cancel'] else False

    def _compute_show_btn_temporary_approve(self):
        for request in self:
            request.show_btn_temporary_approve = False
            existing_approver = request.multi_approvers_ids.filtered(
                lambda r: r.x_approval_seq > request.x_current_sequence).mapped('x_approval_user_ids')
            if self.env.user in existing_approver and request.user_status == 'pending':
                request.show_btn_temporary_approve = True

    def _compute_show_btn_refuse(self):
        for request in self:
            request.show_btn_refuse = False
            if request.request_status == 'pending' and request.user_status == 'pending':
                if request.category_id.x_is_multiple_approval:
                    existing_approver = list(set(request.multi_approvers_ids.filtered(
                        lambda r: r.x_approval_seq >= request.x_current_sequence).mapped('x_approval_user_ids')))
                    if self.env.user in existing_approver:
                        request.show_btn_refuse = True
                else:
                    if self.env.user in request.approver_ids.mapped('user_id'):
                        request.show_btn_refuse = True

    def _compute_show_btn_approve(self):
        for request in self:
            request.show_btn_approve = False
            if request.request_status == 'pending' and request.user_status == 'pending':
                if request.category_id.x_is_multiple_approval:
                    current_step_approvers = request.multi_approvers_ids.filtered(
                        lambda r: r.x_approval_seq == request.x_current_sequence).x_approval_user_ids
                    if self.env.user in current_step_approvers:
                        request.show_btn_approve = True
                else:
                    if self.env.user in request.approver_ids.mapped('user_id'):
                        request.show_btn_approve = False

    @api.onchange('category_id', 'request_owner_id')
    def _onchange_category_id(self):
        if self.x_is_multiple_approval:
            cate_approvers_ids = self.category_id.multi_approvers_ids
            multi_approvers_ids = self.env['ss_erp.multi.approvers']
            seq = 0
            for multi_approvers_id in cate_approvers_ids:
                seq += 1
                x_approver_group_ids = multi_approvers_id.x_approver_group_ids.ids if multi_approvers_id.x_approver_group_ids else []

                x_approver_group_ids = [(6, 0, x_approver_group_ids)]
                new_vals = {
                    'x_request_id': self.id,
                    'x_approval_seq': seq,
                    'x_user_status': 'new',
                    'x_approver_group_ids': x_approver_group_ids,
                    'x_related_group_ids': [(6, 0,
                                             multi_approvers_id.x_related_group_ids.ids)] if multi_approvers_id.x_related_group_ids else False,
                    'x_is_manager_approver': multi_approvers_id.x_is_manager_approver,
                    'x_minimum_approvers': multi_approvers_id.x_minimum_approvers,
                }
                if len(x_approver_group_ids) > 0:
                    multi_approvers_ids += self.env['ss_erp.multi.approvers'].new(new_vals)
            self.multi_approvers_ids = multi_approvers_ids
        else:
            super(ApprovalRequest, self)._onchange_category_id()

    def _generate_approver_ids(self):
        new_users = []
        for line in self.multi_approvers_ids:
            line_approver_ids = []
            if line.x_is_manager_approver:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', self.env.user.id)], limit=1)
                if employee.parent_id.user_id and employee.parent_id.user_id.id not in new_users:
                    line_approver_ids.append(employee.parent_id.user_id.id)
                    new_users.append(employee.parent_id.user_id.id)

            # 承認ユーザ
            for group in line.x_approver_group_ids:
                for user in group.users:
                    if user.id not in new_users:
                        if not line.x_is_own_branch_only:
                            new_users.append(user.id)
                            line_approver_ids.append(user.id)
                        else:
                            if self.x_organization_id in user.organization_ids:
                                new_users.append(user.id)
                                line_approver_ids.append(user.id)
            line.write({'x_approval_user_ids': [(6, 0, line_approver_ids)]})

            line_related_ids = []
            for group in line.x_related_group_ids:
                line_related_ids += group.users.ids
            line.write({'x_related_user_ids': [(6, 0, line_related_ids)]})

        self.write({'approver_ids': [(5, 0, 0)] + [(0, 0, {'user_id': user_id, 'request_id': self.id, 'status': 'new'})
                                                   for user_id in new_users]})

    def _validate_before_confirm(self):
        if not self.x_is_multiple_approval and len(self.approver_ids) < self.approval_minimum:
            raise UserError(
                _("申請の承認をするには、少なくとも%s承認者を追加する必要があります。", self.approval_minimum))
        if self.request_owner_id != self.env.user:
            raise UserError(_("申請者以外は申請することができません。"))
        if self.requirer_document == 'required' and not self.attachment_number:
            raise UserError(_("少なくとも１つのドキュメントを添付する必要はあります。"))
        self.write({'date_confirmed': fields.Datetime.now()})

    def _create_activity_for_approver(self):
        approvers = self.mapped('approver_ids').filtered(lambda approver: approver.status == 'new')
        approvers.write({'status': 'pending'})
        approvers.filtered(lambda x: x.status == 'pending')._create_activity()

    def _change_request_state(self):
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

        if self.x_product_template_form_id:
            self.x_product_template_form_id.write(
                {'approval_id': self.id, 'approval_state': self.request_status})

    # Override
    def action_confirm(self):
        self._validate_before_confirm()

        if self.x_is_multiple_approval:
            self._generate_approver_ids()
            self.multi_approvers_ids.write({'x_user_status': 'pending'})

        self._create_activity_for_approver()
        self._change_request_state()

        user = self.multi_approvers_ids.mapped('x_related_group_ids').mapped('users')
        self.notify_approval(users=user)

    def _approve_multi_approvers(self, user):
        curren_multi_approvers = self.multi_approvers_ids.filtered(lambda p: user in p.x_approval_user_ids)
        if curren_multi_approvers:

            # 現ステップにて、承認済みの数は最小限承認人数を上回る場合、次のステップに進む
            current_approved_users = self.approver_ids.filtered(
                lambda x: x.status == 'approved' and x.user_id in curren_multi_approvers.mapped('x_approval_user_ids'))
            if len(current_approved_users) >= curren_multi_approvers.x_minimum_approvers \
                    and len(current_approved_users) > 0:
                curren_multi_approvers.write({'x_user_status': 'approved'})

            users = curren_multi_approvers.mapped('x_approval_user_ids') - current_approved_users.mapped('user_id')
            self.notify_approval(users=users, approver=self.env.user)

            # 次のステップはある場合、そのステップの承認者たちに通知
            if curren_multi_approvers.x_user_status == 'approved':
                next_multi_approvers = self.multi_approvers_ids.filtered(
                    lambda p: p.x_approval_seq == curren_multi_approvers.x_approval_seq + 1)
                if next_multi_approvers:
                    users = next_multi_approvers.mapped('x_approval_user_ids')
                    self.notify_approval(users=users, approver=self.env.user)

    def action_approve(self, approver=None):
        super(ApprovalRequest, self).action_approve(approver=approver)
        if self.x_is_multiple_approval:
            self._approve_multi_approvers(self.env.user)
        self.sudo().write({'last_approver': self.env.user.id})

    def _refuse_multi_approvers(self):
        curren_multi_approvers = self.multi_approvers_ids.filtered(
            lambda p: self.env.user in p.x_approval_user_ids)
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
            raise UserError(_("申請者以外は取下げすることができません。"))
        super(ApprovalRequest, self).action_draft()
        if self.x_is_multiple_approval:
            self.multi_approvers_ids.write({'x_user_status': 'new'})
        self.activity_ids.sudo().unlink()

    def _cancel_multi_approvers(self):
        self.multi_approvers_ids.write({'x_user_status': 'cancel'})
        self.activity_ids.sudo().unlink()

    def action_cancel(self):
        self.sudo()._get_user_approval_activities(user=self.env.user).unlink()
        super(ApprovalRequest, self).action_cancel()
        if self.x_is_multiple_approval:
            self._cancel_multi_approvers()
        self.activity_ids.sudo().unlink()

    def action_temporary_approve(self):
        if self.x_is_multiple_approval:
            self.action_approve()

            # 前のステップのステータスを承認に変更
            previous_user_ids = self.multi_approvers_ids.filtered(
                lambda r: r.x_approval_seq < self.x_user_sequence).sudo().write({'x_user_status': 'approved'})

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
            users = request.multi_approvers_ids.mapped('x_related_user_ids')
            users |= request.request_owner_id
            self.notify_approval(users=users, approver=request.last_approver)

    def write(self, vals):
        res = super(ApprovalRequest, self).write(vals)

        # LPガス棚卸伝票
        if self.x_lpgas_inventory_ids:
            if self.request_status == 'pending':
                self.x_lpgas_inventory_ids.sudo().write({'state': 'approval'})
            elif self.request_status == 'approved':
                self.x_lpgas_inventory_ids.sudo().write({'state': 'approved'})
            elif self.request_status == 'cancel':
                self.x_lpgas_inventory_ids.sudo().write({'state': 'cancel'})

        # 棚卸更新
        if self.request_status == 'approved':
            if self.category_id.approval_type in ['inventory_request', 'inventory_request_manager']:
                if self.x_inventory_order_ids:
                    self.x_inventory_order_ids.write({
                        'state': 'done'
                    })
                    self.x_inventory_order_ids.mapped('instruction_order_id').write({
                        'state': 'waiting'
                    })
                if self.x_inventory_instruction_ids:
                    self.x_inventory_instruction_ids.write({
                        'state': 'approved'
                    })

        # 工事
        if self.x_construction_order_id:
            if self.request_status == 'approved':
                self.x_construction_order_id.sudo().write({'state': 'confirmed'})
            elif self.request_status == 'pending':
                self.x_construction_order_id.sudo().write({'state': 'request_approve'})
            elif self.request_status == 'refused':
                self.x_construction_order_id.sudo().write({'state': 'cancel'})

        # 仕入先フォーム更新
        if self.x_contact_form_id:
            self.x_contact_form_id.sudo().write({'approval_state': self.request_status})

        # プロダクト申請フォーム
        if self.x_product_template_form_id:
            self.x_product_template_form_id.sudo().write({'approval_state': self.request_status})

        # 見積・受注更新
        if self.x_sale_order_ids:
            if self.request_status == 'approved':
                self.x_sale_order_ids.sudo().write({'approval_status': 'approved'})
            elif self.request_status == 'pending':
                self.x_sale_order_ids.sudo().write({'approval_status': 'in_process'})

        # 仕入請求伝票
        if self.x_account_move_ids:
            if self.request_status == 'approved':
                self.x_account_move_ids.sudo().write({'state': 'posted'})

        return res

    def notify_approval(self, users, approver=None):
        # message_subscribe

        partner_ids = users.mapped('partner_id').ids
        body_template = self.env.ref('ss_erp_approval.message_multi_approver_assigned')
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
