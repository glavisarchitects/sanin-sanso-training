# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountReceiptNotificationHeader(models.Model):
    _name = 'ss_erp.account.receipt.notification.header'
    _description = '全銀振込入金通知結果結果ヘッダ'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    upload_date = fields.Datetime('アップロード日時', index=True,
                                  default=fields.Datetime.now)
    name = fields.Char('名称')
    user_id = fields.Many2one('res.users', '担当者', index=True)
    branch_id = fields.Many2one('ss_erp.organization', '支店', index=True)
    status = fields.Selection(selection=[
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり')
    ], compute='_compute_status', string='ステータス', default="wait", store=True)

    data_class = fields.Char(string='データ区分')
    type_code = fields.Char(string='種別コード')
    acc_from_date = fields.Char(string='勘定日（自）')
    acc_to_date = fields.Char(string='勘定日（至）')
    bank_id = fields.Char(string='金融機関番号')
    bank_branch_number = fields.Char(string='取引支店番号')
    acc_type = fields.Char(string='預金種別')
    acc_number = fields.Char(string='口座番号')
    acc_name = fields.Char(string='口座名')
    account_receipt_notification_header_ids = fields.One2many(
        comodel_name="ss_erp.account.receipt.notification.line",
        inverse_name="account_receipt_notification_header_id",
        string='全銀振込入金通知結果ヘッダ'
    )

    @api.depends('account_receipt_notification_header_ids.status')
    def _compute_status(self):
        for rec in self:
            rec.status = 'wait'
            if rec.account_receipt_notification_header_ids:
                status_list = rec.account_receipt_notification_header_ids.mapped('status')
                if 'error' in status_list:
                    rec.status = 'error'
                elif 'wait' in status_list:
                    rec.status = 'wait'
                else:
                    rec.status = 'success'

    def action_import(self):
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "import",
            "params": {
                "model": "ss_erp.account.receipt.notification.line",
                "context": {
                    "default_account_receipt_result_header_id": self.id,
                },
            }
        }


    def processing_execution(self):
        pass
        # account_receipt = self.account_receipt_notification_header_ids.search([('status', '=', 'wait')])
        # for ac in account_receipt:
        #     partner = self.env['res.partner'].search([])
        #     partner_invoice = self.env['account.move'].search(
        #         [('move_type', '=', 'out_invoice'), ('x_organization_id', '=', self.branch_id.id),
        #          ('x_receipt_type', '=', 'bank'), ('x_is_fb_created', '=', True),
        #          ('x_is_not_create_fb', '=', False),
        #          ('state', '=', 'posted'), ('payment_state', '=', 'not_paid'), ('partner_id', '=', partner.name),
        #          ('amount_total', '=', int(ac.withdrawal_amount)), ])


class AccountReceiptNotificationLine(models.Model):
    _name = 'ss_erp.account.receipt.notification.line'
    _description = '全銀振込入金通知結果結果データ'

    account_receipt_notification_header_id = fields.Many2one('ss_erp.account.receipt.notification.header',
                                                             string='全銀振込入金通知結果ヘッダ')
    status = fields.Selection(selection=[
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラー')
    ], string='ステータス', default='wait', index=True)
    processing_date = fields.Datetime('処理日時', index=True)

    reference_number = fields.Char(string='照会番号')
    account_date = fields.Char(string='勘定日')
    starting_date = fields.Char(string='起算日')
    transfer_amount = fields.Char(string='金額')
    other_ticket_amount = fields.Char(string='うち他店券金額')
    transfer_client_code = fields.Char(string='振込依頼人コード')
    transfer_client_name = fields.Char(string='振込依頼人名')
    bank_name = fields.Char(string='仕向銀行名')
    bank_branch_name = fields.Char(string='仕向支店名')
    cancel_code = fields.Char(string='取消区分')
    edi_information = fields.Char(string='EDI情報')
    dummy = fields.Char(string='ダミー')
    error_message = fields.Char(string='エラーメッセージ')
    payment_id = fields.Many2one('account.payment', string='支払参照')


