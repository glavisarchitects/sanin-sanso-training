# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

CATEGORY_SELECTION = [
    ('required', '必須'),
    ('optional', 'オプション'),
    ('no', 'なし')]


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    has_x_organization = fields.Selection(
        CATEGORY_SELECTION, string="申請組織", default="no", )
    has_x_department = fields.Selection(
        CATEGORY_SELECTION, string="申請部署", default="no", )
    has_x_reject = fields.Selection(
        CATEGORY_SELECTION, string="却下理由", default="no", )
    has_x_contact_form_id = fields.Selection(
        CATEGORY_SELECTION, string="連絡先申請フォーム", default="no", )
    has_x_inventory_order_ids = fields.Selection(
        CATEGORY_SELECTION, string="棚卸伝票", default="no", )
    has_x_sale_order_ids = fields.Selection(
        CATEGORY_SELECTION, string="見積伝票", default="no", )
    has_x_account_move_ids = fields.Selection(
        CATEGORY_SELECTION, string="仕入請求伝票", default="no", )
    x_is_multiple_approval = fields.Boolean(
        string='多段階承認', default=False)
    multi_approvers_ids = fields.Many2many('ss_erp.multi.approvers', column1='approval_categ_id',
                                           column2='multi_approver_id', string='多段階承認',
                                           domain="[('x_request_id', '=', False)]")
    has_x_payment_date = fields.Selection(
        CATEGORY_SELECTION, string="請求書期日", default="no", )
    has_x_purchase_material = fields.Selection(
        CATEGORY_SELECTION, string="仕入商材", default="no", )
    has_x_cash_amount = fields.Selection(
        CATEGORY_SELECTION, string="現金仕入額", default="no", )
    has_x_cash_payment_date = fields.Selection(
        CATEGORY_SELECTION, string="現金支払日", default="no", )
    has_x_prepay_amount = fields.Selection(
        CATEGORY_SELECTION, string="前払仕入額", default="no", )
    has_x_prepay_payment_date = fields.Selection(
        CATEGORY_SELECTION, string="前払支払日", default="no", )
    has_x_payment_reason = fields.Selection(
        CATEGORY_SELECTION, string="支払理由", default="no", )
    has_x_purchase_order_ids = fields.Selection(
        CATEGORY_SELECTION, string="見積依頼伝票", default="no", )
    has_x_transfer_preferred_date = fields.Selection(
        CATEGORY_SELECTION, string="送金希望日", default="no", )
    has_x_present_date = fields.Selection(
        CATEGORY_SELECTION, string="残高現在日", default="no", )
    has_x_cash_balance = fields.Selection(
        CATEGORY_SELECTION, string="現在残高", default="no", )
    has_x_bank_balance = fields.Selection(
        CATEGORY_SELECTION, string="預金残高", default="no", )
    has_x_transfer_date = fields.Selection(
        CATEGORY_SELECTION, string="送金日", default="no", )
    has_x_inventory_instruction_ids = fields.Selection(
        CATEGORY_SELECTION, string="棚卸指示伝票", default="no", )
    approval_type = fields.Selection(selection_add=[
        ('inventory_request', '棚卸'),
        ('inventory_request_manager', '棚卸マネージャー'),
    ])

    @api.onchange('multi_approvers_ids')
    def _on_change_multi_approvers_ids(self):
        """ Auto generate sequence
        """
        for approver in self.multi_approvers_ids:
            if approver != self.multi_approvers_ids[-1] or approver.x_approval_seq != 0:
                continue
            approver.x_approval_seq = len(self.multi_approvers_ids)

