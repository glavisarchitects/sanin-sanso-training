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

    x_request_id = fields.Many2one('approval.request', string='リクエスト', copy=True, store=True)
    x_company_id = fields.Many2one(
        'res.company', related='x_request_id.company_id', readonly=True, copy=False, store=True, index=True,
        string='会社')
    x_existing_request_user_ids = fields.Many2many('res.users')

    x_approval_seq = fields.Integer('番号', default=0)
    x_approver_group_ids = fields.Many2many(comodel_name='res.groups',
                                            relation='ss_erp_approver_group_users_approvers_rel',
                                            column1='approver_id',
                                            column2='group_id', string='承認者グループ',store=True)
    x_related_group_ids = fields.Many2many(comodel_name='res.groups',
                                           relation='ss_erp_related_group_users_approvers_rel',
                                           column1='approver_id', column2='group_id',
                                           string='関係者グループ',store=True)

    x_approval_user_ids = fields.Many2many(comodel_name='res.users',
                                           relation='ss_erp_approver_users_approvers_rel',
                                           column1='approver_id',
                                           column2='user_id', string='承認者',store=True)

    x_related_user_ids = fields.Many2many(comodel_name='res.users',
                                          relation='ss_erp_related_users_approvers_rel',
                                          column1='approver_id', column2='user_id',
                                          string='関係者',store=True)

    x_is_manager_approver = fields.Boolean(
        string='マネージャー承認', store=True, copy=True, default=False)

    x_is_own_branch_only = fields.Boolean(
        string='支店内', copy=True, default=False,
        help='True＝承認者グループ・関係者グループの中で承認申請の組織と一致するユーザーのみ承認者・関係者対象にする,False＝グループに属しているすべてのユーザーを対象にする'
    )

    x_user_status = fields.Selection([
        ('new', '新規'),
        ('pending', '未承認'),
        ('approved', '承認済'),
        ('refused', '却下済'),
        ('cancel', '取消'),
    ], string='ステータス', default='new', readonly=True, store=True, copy=True)
    x_minimum_approvers = fields.Integer('最小限承認人数')
