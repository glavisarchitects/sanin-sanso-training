# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class MultiApprovers(models.Model):
    _name = 'ss_erp.multi.approvers'
    _description = 'Multi Approvers'
    _order = 'x_approval_seq'

    x_company_id = fields.Many2one(
        'res.company', related='x_request_id.company_id', readonly=True, copy=False, store=True, index=True)
    x_create_date = fields.Datetime('Created date', readonly=True,
                                    copy=True, store=True, index=False)
    x_create_uid = fields.Many2one('res.users', string='Author',
                                   readonly=True, copy=True, store=True, index=False)
    x_display_name = fields.Char(string='display name', readonly=True)
    x_existing_request_user_ids = fields.Many2many(
        'res.users', 'existing_request_users_approvers_rel', 'user_id', 'approver_id', string='Existing Request User', readonly=True)
    x_id = fields.Integer(string='ID', readonly=True, copy=True, store=True)
    x_request_id = fields.Many2one('approval.request', string='Request', copy=True, store=True)
    x_write_date = fields.Datetime('Latest update date')
    x_write_uid = fields.Many2one('res.users', string='Last updated')
    x_approval_seq = fields.Integer('Seq.', default=0)
    x_approver_group_ids = fields.Many2many(
        'res.users', 'approver_group_users_approvers_rel', 'user_id', 'approver_id', string='Approver group', store=True, copy=True)
    x_related_user_ids = fields.Many2many(
        'res.users', 'related_users_approvers_rel', 'user_id', 'approver_id', string='Stakeholder group', store=True, copy=True)
    x_is_manager_approver = fields.Boolean(
        string='Manager approval', store=True, copy=True, default=False)
    x_user_status = fields.Selection([
        ('new', 'New'),
        ('pending', 'Unapproved'),
        ('approved', 'Approved'),
        ('refused', 'Rejected'),
        ('cancel', 'Cancel'),
    ], string='status', default='new', readonly=True, store=True, copy=True)
    x_minimum_approvers = fields.Integer('Minimum number of approved people')
    # flag indicating current level of request

    @api.constrains("x_approver_group_ids", "x_minimum_approvers", "x_is_manager_approver")
    def _check_approver_group_minimum_approvers(self):
        for record in self:
            have_manager = 1 if record.x_is_manager_approver else 0
            if len(record.x_approver_group_ids) + have_manager < record.x_minimum_approvers:
                raise UserError(
                    _("You have to add at least %s approvers to multi-approvers.", record.x_minimum_approvers))

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
