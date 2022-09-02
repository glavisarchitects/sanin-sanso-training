# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json


class AccountReceivableList(models.TransientModel):
    _name = 'account.receivable.list'

    due_date_start = fields.Date(string='期日（開始）')
    due_date_end = fields.Date(string='期日（終了）')

    def check_param_config(self):
        r005_form_format_path = self.env['ir.config_parameter'].sudo().get_param('R005_form_format_path')
        if not r005_form_format_path:
            raise UserError('帳票格納先パスの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        r005_form_title = self.env['ir.config_parameter'].sudo().get_param('R005_form_title')
        if not r005_form_title:
            raise UserError('帳票タイトルの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        r005_form_storage_dest_path = self.env['ir.config_parameter'].sudo().get_param('R005_form_storage_dest_path')
        if not r005_form_storage_dest_path:
            raise UserError('帳票タイトルの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

    # 売掛金一覧表作成
    def create_list_of_accounts_receivable(self):
        self.check_param_config()
        # TODO: Recheck token return from svf.cloud.config
        # this is just sample code, need to redo when official information about SVF API is available
        token = self.env['svf.cloud.config'].sudo().get_access_token()

        user_organization = self.env.user.employee_id.organization_first
        invoice_record = self.env['account.move'].search(
            [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),
             ('x_organization_id', '=', user_organization.id), ('invoice_date', '>=', self.due_date_start),
             ('invoice_date', '<=', self.due_date_end), ('state', '=', 'posted'), ])

        payment_record = self.env['account.payment'].search([('reconciled_invoice_ids', 'in', invoice_record.id)])
        # Prepare data sent to SVF
        data = {
            'branch_code': self.env.user.employee_id.organization_first.organization_code,
            'branch_name': self.env.user.employee_id.organization_first.name,
            'customer_code': invoice_record.partner_id.ref,
            'customer_name': invoice_record.partner_id.name,

            # Todo: ss_erp.accounts.receivable.hist? Currently, there is no detailed design on how to get data from this table, only declaring fields
            'receipts': payment_record.amount,
            'earnings': invoice_record.amount_untaxed,
            'consumption_tax': invoice_record.amount_by_group,
            'payment': invoice_record.x_payment_term,
            'conditions': invoice_record.x_receipt_type_branch,

        }
        res = requests.post(
            url='',
            headers='',
            data=json.dumps(data)
        )

        response = res.json()
        if response not in ['202', '303']:
            if response == '400 Bad Request':
                raise UserError('SVF Cloudへの	リクエスト内容が不正です。')
            if response == '401 Unauthorized':
                raise UserError('SVF Cloudの認証情報が不正なです。')
            if response == '403 Forbidden':
                raise UserError('SVF Cloudの実行権限がないか、必要なポイントが足りていません。')
            if response == '429 Too many Requests':
                raise UserError('SVF CloudのAPIコール数が閾値を超えました。')
            if response == '503 Service Unavailable':
                raise UserError('SVF Cloudの同時に処理できる数の制限を超過しました。しばらく時間を置いてから再度実行してください。')
