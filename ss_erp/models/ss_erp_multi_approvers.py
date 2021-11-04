# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class MultiApprovers(models.Model):
    _name = 'ss_erp.multi.approvers'
    _description = 'Multi Approvers'

    x_company_id = fields.Many2one(
        'res.company', related='x_request_id.company_id', readonly=True, copy=False, store=True, index=True)
    x_create_date = fields.Datetime('Created date', readonly=True, copy=True, store=True, index=False)
    x_create_uid = fields.Many2one('res.users', string='Author', readonly=True, copy=True, store=True, index=False)
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
    ], string='status', default='new', readonly=True, store=True, copy=True, compute='_compute_x_user_status')
    x_minimum_approvers = fields.Integer('Minimum number of approved people')

    @api.constrains("x_approver_group_ids", "x_minimum_approvers")
    def _check_approver_group_minimum_approvers(self):
        for record in self:
            if len(record.x_approver_group_ids) < record.x_minimum_approvers:
                raise UserError(_("You have to add at least %s approvers to confirm your request.", record.x_minimum_approvers))

    @api.depends('x_request_id.approver_ids', 'x_request_id.approver_ids.status')
    def _compute_x_user_status(self):
        for multi_approver in self:
            status_lst = multi_approver.x_request_id.mapped('approver_ids.status')
            minimal_approver = multi_approver.x_minimum_approvers if len(status_lst) >= multi_approver.x_minimum_approvers else len(status_lst)
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
            multi_approver.x_user_status = status
