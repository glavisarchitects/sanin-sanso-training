# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class MultiApprovers(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'ss_erp.multi.approvers'
    _description = '多段階承認'
    _order = 'x_approval_seq'

    x_company_id = fields.Many2one(
        'res.company', related='x_request_id.company_id', readonly=True, copy=False, store=True, index=True,string='会社')
    x_display_name = fields.Char(string='表示名', readonly=True)
    x_existing_request_user_ids = fields.Many2many(
        'res.users', 'existing_request_users_approvers_rel', 'user_id', 'approver_id', string='Existing Request User', readonly=True)
    x_request_id = fields.Many2one('approval.request', string='リクエスト', copy=True, store=True)
    x_approval_seq = fields.Integer('Seq.', default=0)
    x_approver_group_ids = fields.Many2many(
        'res.users', 'approver_group_users_approvers_rel', 'user_id', 'approver_id', string='承認者グループ', store=True, copy=True)
    x_related_user_ids = fields.Many2many(
        'res.users', 'related_users_approvers_rel', 'user_id', 'approver_id', string='関係者グループ', store=True, copy=True)
    x_is_manager_approver = fields.Boolean(
        string='マネージャー承認', store=True, copy=True, default=False)
    x_user_status = fields.Selection([
        ('new', '新規'),
        ('pending', '未承認'),
        ('approved', '承認済'),
        ('refused', '却下済'),
        ('cancel', '取消'),
    ], string='status', default='new', readonly=True, store=True, copy=True)
    x_minimum_approvers = fields.Integer('最小限承認人数')

    @api.constrains("x_approver_group_ids", "x_minimum_approvers", "x_is_manager_approver")
    def _check_approver_group_minimum_approvers(self):
        for record in self:
            have_manager = 1 if record.x_is_manager_approver else 0
            if len(record.x_approver_group_ids) + have_manager < record.x_minimum_approvers:
                raise UserError(
                    _("最小限承認数より承認者を追加してください。"))

    def write(self, values):
        res = super(MultiApprovers, self).write(values)

        if 'x_existing_request_user_ids' in values and values.get('x_existing_request_user_ids')[0][0] in [4, 6]:
            for record in self:
                num_approved = len(record.x_existing_request_user_ids)
                minimal_approver = record.x_minimum_approvers
                if num_approved == 1:
                    record.write({'x_user_status': 'pending'})
                if num_approved >= minimal_approver:
                    record.write({'x_user_status': 'approved'})
        return res
