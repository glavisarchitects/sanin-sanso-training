# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.approvals.models.approval_category import CATEGORY_SELECTION


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    has_x_organization = fields.Selection(
        CATEGORY_SELECTION, string="Application organization", default="no",)
    has_x_department = fields.Selection(
        CATEGORY_SELECTION, string="Application department", default="no",)
    has_x_reject = fields.Selection(
        CATEGORY_SELECTION, string="Reason for rejection", default="no",)
    has_x_contact_form_id = fields.Selection(
        CATEGORY_SELECTION, string="Contact application form", default="no",)
    has_x_inventory_order_ids = fields.Selection(
        CATEGORY_SELECTION, string="Inventory slip", default="no",)
    has_x_sale_order_ids = fields.Selection(
        CATEGORY_SELECTION, string="Quotation slip", default="no",)
    has_x_account_move_ids = fields.Selection(
        CATEGORY_SELECTION, string="Purchase request slip", default="no",)
    x_is_multiple_approval = fields.Boolean(
        string='Multi-step approval', default=False)
    multi_approvers_ids = fields.Many2many('ss_erp.multi.approvers', column1='approval_categ_id',
        column2='multi_approver_id', string='Approver setting', domain="[('x_request_id', '=', False)]")
    has_x_payment_date = fields.Selection(
        CATEGORY_SELECTION, string="Invoice date", default="no",)
    has_x_purchase_material = fields.Selection(
        CATEGORY_SELECTION, string="Purchased products", default="no",)
    has_x_cash_amount = fields.Selection(
        CATEGORY_SELECTION, string="Cash purchase amount", default="no",)
    has_x_cash_payment_date = fields.Selection(
        CATEGORY_SELECTION, string="Cash payment date", default="no",)
    has_x_prepay_amount = fields.Selection(
        CATEGORY_SELECTION, string="Prepaid purchase amount", default="no",)
    has_x_prepay_payment_date = fields.Selection(
        CATEGORY_SELECTION, string="Prepaid payment date", default="no",)
    has_x_payment_reason = fields.Selection(
        CATEGORY_SELECTION, string="Reason for payment", default="no",)
    has_x_purchase_order_ids = fields.Selection(
        CATEGORY_SELECTION, string="Quotation request slip", default="no",)
    has_x_transfer_preferred_date = fields.Selection(
        CATEGORY_SELECTION, string="Desired remittance date", default="no",)
    has_x_present_date = fields.Selection(
        CATEGORY_SELECTION, string="Balance current date", default="no",)
    has_x_cash_balance = fields.Selection(
        CATEGORY_SELECTION, string="Current balance", default="no",)
    has_x_bank_balance = fields.Selection(
        CATEGORY_SELECTION, string="Deposit balance", default="no",)
    has_x_transfer_date = fields.Selection(
        CATEGORY_SELECTION, string="Remittance date", default="no",)

    # @api.constrains("multi_approvers_ids", "approval_minimum")
    # def _check_approver_group_minimum_approvers(self):
    #     for record in self:
    #         if record.x_is_multiple_approval and len(record.multi_approvers_ids) < record.approval_minimum:
    #             raise UserError(
    #                 _("You have to add at least %s multi-step approvers.", record.approval_minimum))
