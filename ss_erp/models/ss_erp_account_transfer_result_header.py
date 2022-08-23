# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountTransferResultHeader(models.Model):
    _name = 'ss_erp.account.transfer.result.header'
    _description = '全銀口座振替結果FBファイル取込/新規'
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
    ], string='ステータス', default="wait", store=True)
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
    acc_type = fields.Char(string='預金種別')
    acc_number = fields.Char(string='口座番号')

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
        a005_account_transfer_result_journal_id = self.env['ir.config_parameter'].sudo().get_param(
            'A005_account_transfer_result_journal_id')
        if not a005_account_transfer_result_journal_id:
            raise UserError('仕訳帳情報の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')
        transfer_line = self.account_transfer_result_record_ids.search([('status', '=', 'wait')])
        for tl in transfer_line:
            partner_bank = self.env['res.partner.bank'].search([('bank_bic', '=', tl.withdrawal_bank_number), (
                'x_bank_branch_number', '=', tl.withdrawal_branch_number), ('acc_number', '=', tl.account_number)])
            if not partner_bank:
                tl.status = 'error'
                tl.error_message = '対象の口座情報が見つかりませんでした。'
                continue
            partner = partner_bank.partner_id
            if not partner:
                tl.status = 'error'
                tl.error_message = '対象の口座情報が見つかりませんでした。'
                continue
            partner_invoice = self.env['account.move'].search(
                [('move_type', '=', 'out_invoice'), ('x_organization_id', '=', self.branch_id.id),
                 ('x_more_than_receipts_method', '=', 'transfer'), ('x_is_fb_created', '=', True),
                 ('x_is_not_create_fb', '=', False),
                 ('status', '=', 'posted'), ('payment_state', '=', 'not_paid'), ('partner_id', '=', partner.id),
                 ('amount_total', '=', float(tl.withdrawal_amount)), ])
            if len(partner_invoice) != 1:
                tl.status = 'error'
                if not partner_invoice:
                    tl.error_message = '消込対象の請求情報が見つかりませんでした。'
                if len(partner_invoice) > 1:
                    tl.error_message = '消込対象の請求情報が複数見つかりました。'
                continue
            register_payment = self.env['account.payment.register'].create({
                # 'active_model': 'account.move',
                'active_ids': partner_invoice.id
            })
            register_payment.action_create_payments()
            tl.status = 'success'


class AccountTransferResultLine(models.Model):
    _name = 'ss_erp.account.transfer.result.line'
    _description = '全銀口座振替実績FBインポートデータ'

    account_transfer_result_header_id = fields.Many2one('ss_erp.account.transfer.result.header', string='全銀口座振替結果ヘッダ')
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
    deposit_type = fields.Char(string='預金種目')
    account_number = fields.Char(string='口座番号')
    depositor_name = fields.Char(string='預金者名')
    withdrawal_amount = fields.Char(string='引落金額')
    new_code = fields.Char(string='新規コード')
    customer_number = fields.Char(string='顧客番号')
    transfer_result_code = fields.Char(string='振込結果コード')
    dummy2 = fields.Char(string='ダミー２')
    error_message = fields.Char(string='エラーメッセージ')
    payment_id = fields.Many2one('account.payment', string='支払参照')
