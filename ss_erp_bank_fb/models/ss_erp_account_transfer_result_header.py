# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools import format_date


class AccountTransferResultHeader(models.Model):
    _name = 'ss_erp.account.transfer.result.header'
    _description = '全銀口座振替結果FBファイル取込/新規'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    upload_date = fields.Datetime('アップロード日時', index=True,
                                  default=fields.Datetime.now)
    name = fields.Char('名称', copy=False)
    user_id = fields.Many2one('res.users', '担当者', index=True)
    branch_id = fields.Many2one('ss_erp.organization', '支店', index=True)
    status = fields.Selection(selection=[
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり')
    ], compute='_compute_status', string='ステータス', default="wait", store=True)
    account_transfer_result_record_ids = fields.One2many(
        comodel_name="ss_erp.account.transfer.result.line",
        inverse_name="account_transfer_result_header_id",
    )
    # has_data_import = fields.Boolean(compute='_compute_has_data_import')
    data_class = fields.Char(string='データ区分')
    type_code = fields.Char(string='種別コード')
    entruster_code = fields.Char(string='委託者コード')
    entruster_name = fields.Char(string='委託者名')
    withdrawal_date = fields.Char(string='引落日')
    bank_id = fields.Char(string='金融機関番号')
    bank_branch_number = fields.Char(string='取引支店番号')
    acc_type = fields.Selection([("1", "普通"), ("2", "当座")], string='預金種目')
    acc_number = fields.Char(string='口座番号')

    @api.model
    def create(self, vals):
        exist_name = self.env['ss_erp.account.transfer.result.header'].search([]).mapped('name')
        if vals.get("name") in exist_name:
            raise UserError('名称は既に存在します。別の名前を付けてください')
        result = super(AccountTransferResultHeader, self).create(vals)
        return result

    def write(self, vals):
        exist_name = self.env['ss_erp.account.transfer.result.header'].search([]).mapped('name')
        if vals.get('name') in exist_name:
            raise UserError('名称は既に存在します。別の名前を付けてください')
        return super(AccountTransferResultHeader, self).write(vals)

    @api.depends('account_transfer_result_record_ids.status')
    def _compute_status(self):
        for rec in self:
            rec.status = 'wait'
            if rec.account_transfer_result_record_ids:
                status_list = rec.account_transfer_result_record_ids.mapped('status')
                if 'error' in status_list:
                    rec.status = 'error'
                elif 'wait' in status_list:
                    rec.status = 'wait'
                else:
                    rec.status = 'success'

    def action_import(self):
        self.ensure_one()
        self.upload_date = fields.Datetime.now()
        return {
            "type": "ir.actions.client",
            "tag": "import",
            "params": {
                "model": "ss_erp.account.transfer.result.line",
                "context": {
                    "default_account_transfer_result_header_id": self.id,
                },
            }
        }

    def processing_execution(self):
        # Todo: journal will be created with data
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
        # journal_account_1121 = self.env['account.journal'].search([('default_account_id', '=', account_1121.id)], limit=1)
        #
        # account_1122 = self.env['account.account'].search([('code', '=', '1122')], limit=1)
        # journal_account_1122 = self.env['account.journal'].search([('default_account_id', '=', account_1122.id)], limit=1)
        #
        # if not account_1121 or not account_1122:
        #     raise UserError('アカウント1122とか1121が見つかりません。設定してください。')
        #
        # if not journal_account_1121 or not journal_account_1122:
        #     raise UserError('ジャーナル 1121 または 1122 が見つかりません。')

        transfer_line = self.account_transfer_result_record_ids.search([('status', '=', 'wait')])
        for tl in transfer_line:
            if tl.deposit_type == '1':
                journal_id = journal_account_1122
            else:
                journal_id = journal_account_1121
            bank = self.env['res.bank'].search([('bic', '=', tl.withdrawal_bank_number)], limit=1)
            partner_bank = self.env['res.partner.bank'].search([('bank_id', '=', bank.id), (
                'x_bank_branch_number', '=', tl.withdrawal_branch_number), ('acc_number', '=', tl.account_number)])
            if not partner_bank:
                tl.status = 'error'
                tl.error_message = '対象の口座情報が見つかりませんでした。'
                continue
            partner = partner_bank.partner_id
            if not partner:
                tl.status = 'error'
                tl.error_message = '対象の顧客情報が見つかりませんでした。'
                continue
            partner_invoice = self.env['account.move'].search(
                [('move_type', '=', 'out_invoice'), ('x_organization_id', '=', self.branch_id.id),
                 ('x_receipt_type', '=', 'bank'), ('x_is_fb_created', '=', True),
                 ('x_is_not_create_fb', '=', False),
                 ('state', '=', 'posted'), ('payment_state', '=', 'not_paid'), ('partner_id', '=', partner.id),
                 ('amount_total', '=', int(tl.withdrawal_amount)), ])
            if len(partner_invoice) != 1:
                tl.status = 'error'
                if not partner_invoice:
                    tl.error_message = '消込対象の請求情報が見つかりませんでした。'
                if len(partner_invoice) > 1:
                    tl.error_message = '消込対象の請求情報が複数見つかりました。'
                continue
            # register_payment = partner_invoice.action_register_payment()
            register_payment = self.env['account.payment.register'].with_context(
                active_model='account.move',
                active_ids=[partner_invoice.id],
                active_id=partner_invoice.id,
                allowed_company_ids=[partner_invoice.company_id.id],
                dont_redirect_to_payments=True).create(
                {
                    # 'active_model': 'account.move',
                    # 'active_ids': partner_invoice.id,
                    'journal_id': int(journal_id),
                    # 'amount': partner_invoice.amount_total,
                    # 'payment_date': fields.Date.context_today,
                    # 'company_id': partner_invoice.company_id.id,
                })
            register_payment.sudo().action_create_payments()
            # assign payment_id
            created_payment = self.env['account.payment'].search([('ref', '=', partner_invoice.name)], limit=1)
            # 09/13/2022
            # Year + Withdrawal date in account transfer result header (yyyy/mm/dd)
            year_current = datetime.today().year
            withdrawal_date = (str(self.withdrawal_date) + str(year_current)) if self.withdrawal_date else False
            date_acc_payment = datetime.strptime(withdrawal_date, '%m%d%Y')

            in_accounts_receivable = self.env['account.account'].search([('code', '=', '1150')])
            receivable_line = partner_invoice.line_ids.filtered(
                lambda l: l.account_id.user_type_id.type == 'receivable')
            if not in_accounts_receivable:
                raise UserError('アカウント 1150 が見つかりません。設定してください。')

            created_payment.move_id.sudo().write({
                'x_receipt_type': partner_invoice.x_receipt_type,
                'x_payment_type': partner_invoice.x_payment_type,
                'x_organization_id': partner_invoice.x_organization_id,
                'x_responsible_dept_id': partner_invoice.x_responsible_dept_id,
                'x_is_not_create_fb': True,
                # 'date': self.upload_date,
                'date': date_acc_payment,
                # 'journal_id': self.env['account.journal'].browse(int(a005_account_transfer_result_journal_id)),
                'x_responsible_user_id': partner_invoice.x_responsible_user_id,
                'x_mkt_user_id': partner_invoice.x_mkt_user_id,
                'x_is_fb_created': False,

            })

            created_payment.sudo().write(
                {
                    'x_receipt_type': partner_invoice.x_receipt_type,
                    'x_payment_type': partner_invoice.x_payment_type,
                    'x_sub_account_id': receivable_line.x_sub_account_id,
                    'x_organization_id': partner_invoice.x_organization_id,
                    'x_responsible_dept_id': partner_invoice.x_responsible_dept_id,
                    'x_is_not_create_fb': True,
                    'x_is_fb_created': False,
                })

            debit_line = created_payment.move_id.line_ids.filtered(lambda l: l.debit > 0)
            debit_line.date_maturity = self.upload_date

            credit_line = created_payment.move_id.line_ids.filtered(lambda l: l.credit > 0)

            # if tl.deposit_type == '1':
            #     deposit_account = account_1122
            # else:
            #     deposit_account = account_1121
            #
            # debit_line.account_id = deposit_account.id

            # in_accounts_receivable = self.env['account.account'].search([('code', '=', '1150')])
            # receivable_line = partner_invoice.line_ids.filtered(
            #     lambda l: l.account_id.user_type_id == self.env.ref('account.data_account_type_receivable').id)
            # if not in_accounts_receivable:
            #     raise UserError('アカウント 1150 が見つかりません。設定してください。')
            # credit_line.account_id = in_accounts_receivable.id
            # credit_line.x_sub_account_id = receivable_line.x_sub_account_id
            # credit_line.date_maturity = self.upload_date

            credit_line.with_context({
                'from_zengin_create': True,
            }).write({
                'account_id': in_accounts_receivable.id,
                'x_sub_account_id': receivable_line.x_sub_account_id,
                'date_maturity': self.upload_date,
            })

            tl.payment_id = created_payment.id
            tl.status = 'success'


class AccountTransferResultLine(models.Model):
    _name = 'ss_erp.account.transfer.result.line'
    _description = '全銀口座振替実績FBインポートデータ'

    account_transfer_result_header_id = fields.Many2one('ss_erp.account.transfer.result.header',
                                                        string='全銀口座振替結果ヘッダ')
    status = fields.Selection(selection=[
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラー')
    ], string='ステータス', default="wait")
    processing_date = fields.Datetime('処理日時', index=True)
    withdrawal_bank_number = fields.Char(string='引落銀行番号')
    withdrawal_bank_name = fields.Char(string='引落銀行名')
    withdrawal_branch_number = fields.Char(string='引落支店番号')
    withdrawal_branch_name = fields.Char(string='引落支店名')
    dummy1 = fields.Char(string='ダミー１')
    deposit_type = fields.Selection([("1", "普通"), ("2", "当座")], string='預金種目')
    account_number = fields.Char(string='口座番号')
    depositor_name = fields.Char(string='預金者名')
    withdrawal_amount = fields.Char(string='引落金額')
    new_code = fields.Char(string='新規コード')
    customer_number = fields.Char(string='顧客番号')
    transfer_result_code = fields.Char(string='振込結果コード')
    dummy2 = fields.Char(string='ダミー２')
    error_message = fields.Char(string='エラーメッセージ')
    payment_id = fields.Many2one('account.payment', string='支払参照')
