# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_organization_id = fields.Many2one('ss_erp.organization', string='組織')

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        approval_account_move_in = self.env['approval.request'].search([('x_account_move_ids', 'in', self.id),
                                                                        ('request_status', 'not in',
                                                                         ['cancel', 'refuse'])])
        if approval_account_move_in and self.move_type == 'in_invoice':
            for approval in approval_account_move_in:
                if len(approval.x_account_move_ids) > 1:
                    message = '仕入請求伝票%sが見積操作で取消されたため、承認申請から削除されました。' % self.name
                    approval.sudo().write({'x_account_move_ids': [(3, self.id)]})
                    approval.message_post(body=message)
                else:
                    approval.sudo().update({
                        'request_status': 'cancel',
                    })
                    approval.message_post(body=_('承認申請の仕入請求伝票が仕入請求操作で取消されたため、承認申請を取消しました。'))
        return res

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
        # if token["response"] == 200:
        #     pass
        #     if token.response == '400 Bad Request':
        #         raise UserError('SVF Cloudへの	リクエスト内容が不正です。')
        #     if token.response == '401 Unauthorized':
        #         raise UserError('SVF Cloudの認証情報が不正なです。')
        #     if token.response == '403 Forbidden':
        #         raise UserError('SVF Cloudの実行権限がないか、必要なポイントが足りていません。')
        #     if token.response == '429 Too many Requests':
        #         raise UserError('SVF CloudのAPIコール数が閾値を超えました。')
        #     if token.response == '503 Service Unavailable':
        #         raise UserError('SVF Cloudの同時に処理できる数の制限を超過しました。しばらく時間を置いてから再度実行してください。')

        # Prepare data sent to SVF
        data = {
            # '請求書': self.name,
            'partner_invoice_id': self.partner_invoice_id.name,
            'key': self.env['ir.config_parameter'].sudo().get_param('invoice_report.registration_number'),
            'name': self.partner_id.name,
            'responsible_person': self.x_organization_id.responsible_person,
            'zip': self.partner_id.zip,
            'state': self.partner_id.state_id.name,
            'city': self.partner_id.city,
            'street': self.partner_id.street,
            'street2': self.partner_id.street2,
            'phone': self.partner_id.phone,
            'x_fax': self.partner_id.x_fax,
            'invoice_date_due': self.invoice_date_due,
            'amount_total': self.amount_total,
            'debit': self.debit,
            'date_done': self.date_done,
        }
        res = requests.post(
            url='',
            headers='',
            data=json.dumps(data)
        )

    # End Region
