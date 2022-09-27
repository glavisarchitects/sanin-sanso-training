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
    acc_type = fields.Selection([("1", "普通"), ("2", "当座"), ("4", "貯蓄預金")], string='預金種目')
    acc_number = fields.Char(string='口座番号')
    acc_name = fields.Char(string='口座名')
    account_receipt_notification_header_ids = fields.One2many(
        comodel_name="ss_erp.account.receipt.notification.line",
        inverse_name="account_receipt_notification_header_id",
        string='全銀振込入金通知結果ヘッダ'
    )

    @api.model
    def create(self, vals):
        exist_name = self.env['ss_erp.account.receipt.notification.header'].search([]).mapped('name')
        if vals.get("name") in exist_name:
            raise UserError('名称は既に存在します。別の名前を付けてください')
        result = super(AccountReceiptNotificationHeader, self).create(vals)
        return result

    def write(self, vals):
        exist_name = self.env['ss_erp.account.receipt.notification.header'].search([]).mapped('name')
        if vals.get('name') in exist_name:
            raise UserError('名称は既に存在します。別の名前を付けてください')
        return super(AccountReceiptNotificationHeader, self).write(vals)

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
    name = fields.Char('名称', realated='account_receipt_notification_header_id.name',store=True)
    user_id = fields.Many2one('res.users', related='account_receipt_notification_header_id.user_id')
    branch_id = fields.Many2one('ss_erp.organization', related='account_receipt_notification_header_id.branch_id',
                                string='支店')

    status = fields.Selection(selection=[
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラー')
    ], string='ステータス', default='wait', index=True)
    processing_date = fields.Datetime('処理日時', default=lambda self: fields.Datetime.now(), index=True)

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
                                               domain="[('state', '=', 'posted'),  'in', ('not_paid','partial'),",
                                               string='支払参照')

    def processing_execution(self):
        total_amount = sum(self.result_account_move_ids.mapped('amount_residual'))
        if total_amount != int(self.transfer_amount):
            raise UserError('選択したすべての請求書の送金金額と合計金額が等しくありません。再度確認してください。')

        # if self.account_receipt_notification_header_id.acc_type not in ['1', '2']:
        #     raise UserError('預金種目は普通と当座だけ受け入れられます。')

        a005_account_transfer_result_journal_id = self.env['ir.config_parameter'].sudo().get_param(
            'A005_account_transfer_result_journal_id')
        if not a005_account_transfer_result_journal_id:
            raise UserError('仕訳帳情報の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        journal_ids = a005_account_transfer_result_journal_id.split(",")
        if len(journal_ids) != 2:
            raise UserError('仕訳帳情報の設定は間違っています。もう一度ご確認してください。')
        # 当座預金
        journal_account_1121 = journal_ids[0]
        # 普通預金
        journal_account_1122 = journal_ids[1]


        # account_1121 = self.env['account.account'].search([('code', '=', '1121')], limit=1)
        # journal_account_1121 = self.env['account.journal'].search([('default_account_id', '=', account_1121.id)],
        #                                                           limit=1)
        #
        # account_1122 = self.env['account.account'].search([('code', '=', '1122')], limit=1)
        # journal_account_1122 = self.env['account.journal'].search([('default_account_id', '=', account_1122.id)],
        #                                                           limit=1)

        if self.account_receipt_notification_header_id.acc_type == '1':
            journal_id = journal_account_1122
        else:
            journal_id = journal_account_1121

        # Register multi payment
        register_payment = self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=self.result_account_move_ids.ids,
            dont_redirect_to_payments=True).create(
            {
                # 'active_model': 'account.move',
                # 'active_ids': partner_invoice.id,
                'journal_id': journal_id.id,
                # 'amount': partner_invoice.amount_total,
                # 'payment_date': fields.Date.context_today,
                # 'company_id': partner_invoice.company_id.id,
            })
        register_payment.sudo().action_create_payments()
        # assign payment_id
        # ref_invoice = self.result_account_move_ids.mapped('name')
        # created_payment = self.env['account.payment'].search([('ref', 'in', ref_invoice)],).ids
        created_payment_ids = []
        for invoice in self.result_account_move_ids:
            created_payment = self.env['account.payment'].search([('ref', '=', invoice.name)], )
            created_payment.move_id.write(
                {
                    'x_receipt_type': invoice.x_receipt_type,
                    'x_payment_type': invoice.x_payment_type,
                    'x_organization_id': invoice.x_organization_id,
                    'x_responsible_dept_id': invoice.x_responsible_dept_id,
                    'x_is_not_create_fb': True,
                    'date': self.account_receipt_notification_header_id.upload_date,
                    'x_responsible_user_id': invoice.x_responsible_user_id,
                    'x_mkt_user_id': invoice.x_mkt_user_id,
                    'x_is_fb_created': False,
                })

            debit_line = created_payment.move_id.line_ids.filtered(lambda l: l.debit > 0)
            debit_line.date_maturity = self.account_receipt_notification_header_id.upload_date

            credit_line = created_payment.move_id.line_ids.filtered(lambda l: l.credit > 0)

            # if tl.deposit_type == '1':
            #     deposit_account = account_1122
            # else:
            #     deposit_account = account_1121
            #
            # debit_line.account_id = deposit_account.id

            in_accounts_receivable = self.env['account.account'].search([('code', '=', '1150')])
            receivable_line = invoice.line_ids.filtered(
                lambda l: l.account_id.user_type_id == self.env.ref('account.data_account_type_receivable').id)
            if not in_accounts_receivable:
                raise UserError('アカウント 1150 が見つかりません。設定してください。')
            # credit_line.account_id = in_accounts_receivable.id
            # credit_line.x_sub_account_id = receivable_line.x_sub_account_id
            # credit_line.date_maturity = self.upload_date

            credit_line.with_context({
                'from_zengin_create': True,
            }).write({
                'account_id': in_accounts_receivable.id,
                'x_sub_account_id': receivable_line.x_sub_account_id,
                'date_maturity': self.account_receipt_notification_header_id.upload_date,
            })
            created_payment_ids.append(created_payment.id)
        self.payment_ids = created_payment_ids
        self.status = 'success'


