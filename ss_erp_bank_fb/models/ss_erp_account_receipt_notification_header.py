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


class AccountReceiptNotificationLine(models.Model):
    _name = 'ss_erp.account.receipt.notification.line'
    _description = '全銀振込入金通知結果結果データ'

    account_receipt_notification_header_id = fields.Many2one('ss_erp.account.receipt.notification.header',
                                                             string='全銀振込入金通知結果ヘッダ')

    name = fields.Char('名称')
    user_id = fields.Many2one('res.users', related='account_receipt_notification_header_id.user_id')
    branch_id = fields.Many2one('ss_erp.organization', related='account_receipt_notification_header_id.branch_id',
                                string='支店')

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
    payment_ids = fields.Many2many('account.payment', string='支払参照')
    result_account_move_ids = fields.Many2many('account.move',
                                               domain="[('state', '=', 'posted'), ('payment_state', '=', 'not_paid')]",
                                               string='支払参照')

    def search_account_move(self):
        str_customer_name = self.transfer_client_name
        partner_rec = self.env['res.partner']
        receipt_notification_partner = partner_rec.search([('name', 'like', str_customer_name), ], limit=1)
        if not receipt_notification_partner:
            for pa in partner_rec.search([]):
                if pa.name in str_customer_name:
                    receipt_notification_partner = pa
                    break
        if not receipt_notification_partner:
            raise UserError('対象の顧客情報が見つかりませんでした。')

        current_employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        cur_employee_organization = current_employee_id.organization_first
        customer_invoice_rec = self.env['account.move'].search(
            [('partner_id', '=', receipt_notification_partner.id), ('move_type', '=', 'out_invoice'),
             ('x_organization_id', '=', cur_employee_organization.id), ('x_receipt_type', '=', 'bank'),
             ('x_is_fb_created', '=', True), ('x_is_not_create_fb', '=', False), ('state', '=', 'posted'),
             ('payment_state', '=', 'not_paid'), ])

        # ('amount_total', '=', int(self.transfer_amount)),

        self.result_account_move_ids = [(6, 0, customer_invoice_rec.ids)]

    def processing_execution(self):
        total_amount = sum(self.result_account_move_ids.mapped('amount_total_signed'))
        if total_amount != int(self.transfer_amount):
            raise UserError('選択したすべての請求書の送金金額と合計金額が等しくありません。再度確認してください。')

        # Register multi payment
        register_payment = self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=self.result_account_move_ids.ids,
            dont_redirect_to_payments=True).create(
            {
                # 'active_model': 'account.move',
                # 'active_ids': partner_invoice.id,
                # 'journal_id': journal_id.id,
                # 'amount': partner_invoice.amount_total,
                # 'payment_date': fields.Date.context_today,
                # 'company_id': partner_invoice.company_id.id,
            })
        register_payment.sudo().action_create_payments()
        # assign payment_id
        ref_invoice = self.result_account_move_ids.mapped('name')
        created_payment = self.env['account.payment'].search([('ref', 'in', ref_invoice)],).ids
        # created_payment.move_id.write(
        #     {
        #         'x_receipt_type': partner_invoice.x_receipt_type,
        #         'x_payment_type': partner_invoice.x_payment_type,
        #         'x_organization_id': partner_invoice.x_organization_id,
        #         'x_responsible_dept_id': partner_invoice.x_responsible_dept_id,
        #         'x_is_not_create_fb': True,
        #         'date': self.upload_date,
        #         # 'journal_id': self.env['account.journal'].browse(int(a005_account_transfer_result_journal_id)),
        #         'x_responsible_user_id': partner_invoice.x_responsible_user_id,
        #         'x_mkt_user_id': partner_invoice.x_mkt_user_id,
        #         'x_is_fb_created': False,
        #     })
        #
        # debit_line = created_payment.move_id.line_ids.filtered(lambda l: l.debit > 0)
        # debit_line.date_maturity = self.upload_date
        #
        # credit_line = created_payment.move_id.line_ids.filtered(lambda l: l.credit > 0)
        #
        # # if tl.deposit_type == '1':
        # #     deposit_account = account_1122
        # # else:
        # #     deposit_account = account_1121
        # #
        # # debit_line.account_id = deposit_account.id
        #
        # in_accounts_receivable = self.env['account.account'].search([('code', '=', '1150')])
        # receivable_line = partner_invoice.line_ids.filtered(
        #     lambda l: l.account_id.user_type_id == self.env.ref('account.data_account_type_receivable').id)
        # if not in_accounts_receivable:
        #     raise UserError('アカウント 1150 が見つかりません。設定してください。')
        # # credit_line.account_id = in_accounts_receivable.id
        # # credit_line.x_sub_account_id = receivable_line.x_sub_account_id
        # # credit_line.date_maturity = self.upload_date
        #
        # credit_line.with_context({
        #     'zengin_aoo5': True,
        # }).write({
        #     'account_id': in_accounts_receivable.id,
        #     'x_sub_account_id': receivable_line.x_sub_account_id,
        #     'date_maturity': self.upload_date,
        # })

        self.payment_ids = created_payment
        self.status = 'success'
