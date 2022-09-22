# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json


class AccountReceivableBalanceConfirm(models.TransientModel):
    _name = 'account.receivable.balance.confirm'

    return_date = fields.Date(string='返送日')
    close_date = fields.Date(string='返送日')
    partner_id = fields.Many2one('res.partner', string='得意先顧客')

    def check_param_config(self):
        r003_form_format_path = self.env['ir.config_parameter'].sudo().get_param('R003_form_format_path')
        if not r003_form_format_path:
            raise UserError('帳票レイアウトパスの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        R003_form_title = self.env['ir.config_parameter'].sudo().get_param('R003_form_title')
        if not R003_form_title:
            raise UserError('帳票タイトルの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        R003_form_storage_dest_path = self.env['ir.config_parameter'].sudo().get_param('R003_form_storage_dest_path')
        if not R003_form_storage_dest_path:
            raise UserError('帳票格納先パスの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

    def receivable_balance_confirm(self):
        self.check_param_config()
        # TODO: Recheck token return from svf.cloud.config
        # this is just sample code, need to redo when official information about SVF API is available
        token = self.env['svf.cloud.config'].sudo().get_access_token()

        # Todo: Reconfirm the search terms account_move 返送日 and 返送日
        invoice_record = self.env['account.move'].search(
            [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ])
        # Prepare data sent to SVF
        data = {
            'zip': self.partner_id.zip,
            'address': self.partner_id.state_id.name + '' + self.partner_id.street + '' + self.partner_id.street2,
            'customer_name': str(self.partner_id.name) if self.partner_id.name else '' + ' 様',
            'customer_barcode': self.partner_id.state_id.zip + '' + self.partner_id.street + '' + self.partner_id.street2,
            'branch': invoice_record.x_organization_id.name,
            'branch_phone_number': invoice_record.x_organization_id.organization_phone,
            'customer_code': self.partner_id.ref,

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
