# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json


class AccountMove(models.Model):
    _inherit = 'account.move'

    # SVF Region
    def check_param_r002_config(self):
        r002_form_format_path = self.env['ir.config_parameter'].sudo().get_param('R002_form_format_path')
        if not r002_form_format_path:
            raise UserError('帳票レイアウトパスの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        r002_form_title = self.env['ir.config_parameter'].sudo().get_param('R002_form_title')
        if not r002_form_title:
            raise UserError('帳票タイトルの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        r002_form_storage_dest_path = self.env['ir.config_parameter'].sudo().get_param('R002_form_storage_dest_path')
        if not r002_form_storage_dest_path:
            raise UserError('帳票格納先パスの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        r002_form_img_resource_path = self.env['ir.config_parameter'].sudo().get_param('R002_form_img_resource_path')
        if not r002_form_img_resource_path:
            raise UserError('画像パスの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

    def svf_template_export(self):
        self.check_param_r002_config()
        # TODO: Recheck token return from svf.cloud.config
        # this is just sample code, need to redo when official information about SVF API is available
        token = self.env['svf.cloud.config'].sudo().get_access_token()

        # Prepare data sent to SVF
        sale_doc_reference = self.invoice_origin.split(', ')
        so_record = self.env['sale.order'].search([('name', 'in', sale_doc_reference)])
        if not so_record:
            raise UserError('対応する SO レコードが見つかりません。')
        if len(so_record) > 1:
            raise UserError('複数の SO . レコードが見つかりました。')

        payment_record = self.env['account.payment'].search([('ref', 'in', self.name)])
        if not payment_record:
            raise UserError('対応する Payment レコードが見つかりません。')
        if len(payment_record) > 1:
            raise UserError('複数の Payment . レコードが見つかりました。')


        # Todo: wait for account_move_line, sale_order_line data confirmation
        data = {
            # '請求書': self.name,
            'invoice_no': self.partner_invoice_id.name,
            'registration_number': self.env['ir.config_parameter'].sudo().get_param(
                'invoice_report.registration_number'),
            'name': self.x_organization_id.name,
            'responsible_person': self.x_organization_id.responsible_person,
            'zip': so_record.partner_invoice_id.zip,
            'state': so_record.partner_invoice_id.state_id.name,
            'city': so_record.partner_invoice_id.city,
            'organization_zip': self.x_organization_id.organization_zip,
            'organization_address': self.x_organization_id.organization_state_id.name + '' + self.x_organization_id.organization_city + '' + self.x_organization_id.organization_street + '' + self.x_organization_id.organization_street2 + '',
            'organization_phone': self.x_organization_id.organization_phone,
            'organization_fax': self.x_organization_id.organization_fax,
            'invoice_date_due': self.invoice_date_due,
            'amount_total': self.amount_total,
            'debit': self.debit,
            'date_done': self.date_done,
            #  Payment
            'date': payment_record.date,
            'slip_number': payment_record.name,
            'product_name': payment_record.x_receipt_type,
            'price': payment_record.amount,
            'summary': payment_record.x_remarks,
        }
        res = requests.post(
            url='',
            headers='',
            data=json.dumps(data)
        )
        # sale_doc_reference = self.invoice_origin.split(', ')

        response = res.json()
        if response == 200:
            pass
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

    # End Region