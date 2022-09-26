# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import jwt
import datetime
import calendar
import base64

import requests
from urllib.parse import urljoin

import logging

_logger = logging.getLogger(__name__)


class SvfCloudConfig(models.Model):
    _name = 'svf.cloud.config'

    def get_svf_param(self):
        client_id = self.env['ir.config_parameter'].sudo().get_param('svf_cloud_client_id')
        if not client_id:
            raise UserError('SVF Cloud クライアントIDの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        cloud_secret = self.env['ir.config_parameter'].sudo().get_param('svf_cloud_secret')
        if not cloud_secret:
            raise UserError('SVF Cloud シークレットの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        cloud_private_key = self.env['ir.config_parameter'].sudo().get_param('svf_cloud_private_key')
        if not cloud_private_key:
            raise UserError('SVF Cloud 秘密鍵の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        cloud_user_id = self.env['ir.config_parameter'].sudo().get_param('svf_cloud_user_id')
        if not cloud_user_id:
            raise UserError('SVF Cloud ユーザーIDの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        cloud_access_token_exp_sec = self.env['ir.config_parameter'].sudo().get_param('svf_cloud_access_token_exp_sec')
        if not cloud_access_token_exp_sec:
            raise UserError('SVF Cloud アクセストークン有効期限の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        cloud_access_token_req_url = self.env['ir.config_parameter'].sudo().get_param('svf_cloud_access_token_req_url')
        if not cloud_access_token_req_url:
            raise UserError('SVF Cloud アクセストークン取得リクエストURLの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        svf_cloud_access_token_revoke_req_url = self.env['ir.config_parameter'].sudo().get_param('svf_cloud_access_token_revoke_req_url')
        if not svf_cloud_access_token_revoke_req_url:
            raise UserError('SVF Cloud アクセストークン破棄リクエストURLの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        svf_cloud_access_form_output_req_url = self.env['ir.config_parameter'].sudo().get_param(
            'svf_cloud_access_form_output_req_url')
        if not svf_cloud_access_form_output_req_url:
            raise UserError('SVF Cloud 帳票出力リクエストURLの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        result = {
            'client_id': client_id,
            'cloud_secret': cloud_secret,
            'cloud_private_key': cloud_private_key,
            'cloud_user_id': cloud_user_id,
            'cloud_access_token_exp_sec': cloud_access_token_exp_sec,
            'cloud_access_token_req_url': cloud_access_token_req_url,
            'svf_cloud_access_form_output_req_url': svf_cloud_access_form_output_req_url,
        }
        return result

    def check_specific_param_config(self, type_report):
        """type_report eg R002,R003... """
        config = {}
        key_config_form_format_path = type_report + '_form_format_path'
        form_format_path = self.env['ir.config_parameter'].sudo().get_param(key_config_form_format_path)
        if not form_format_path:
            raise UserError('帳票レイアウトパスの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')
        config['form_format_path'] = form_format_path

        key_config_form_title = type_report + '_form_title'
        form_title = self.env['ir.config_parameter'].sudo().get_param(key_config_form_title)
        if not form_title:
            raise UserError('帳票タイトルの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')
        config['form_title'] = form_title

        key_config_form_storage_dest_path = type_report + '_form_storage_dest_path'
        form_storage_dest_path = self.env['ir.config_parameter'].sudo().get_param(key_config_form_storage_dest_path)
        if not form_storage_dest_path:
            raise UserError('帳票格納先パスの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')
        config['form_storage_dest_path'] = form_storage_dest_path

        # key_config_form_img_resource_path = type_report + '_form_img_resource_path'
        # form_img_resource_path = self.env['ir.config_parameter'].sudo().get_param(key_config_form_img_resource_path)
        # if not form_img_resource_path:
        #     raise UserError('画像パスの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')
        # config['form_storage_dest_path'] = form_img_resource_path

        return config

    def get_access_token(self):
        param = self.get_svf_param()
        # time expires in second
        expires = calendar.timegm((datetime.datetime.utcnow() + datetime.timedelta(
            seconds=int(param['cloud_access_token_exp_sec']))).timetuple())

        headers = {
            "alg": "RS256",
        }
        payload = {
            "iss": param['client_id'],
            "sub": param['cloud_user_id'],
            "exp": expires,  # expiration time
            "userName": self.env.user.name,
            # "timeZone": self.env.user.tz or 'Asia/Tokyo',
            "timeZone": 'Asia/Tokyo',
            "locale": 'ja',
        }

        private_key = param['cloud_private_key'].encode('utf-8')
        gen_jwt_token = jwt.encode(payload=payload, key=private_key, headers=headers, algorithm="RS256")

        bearer_token_64 = base64.b64encode(
            ("%s:%s" % (param['client_id'], param['cloud_secret'])).encode('UTF-8')).decode('UTF-8')
        response = requests.post(url=param['cloud_access_token_req_url'],
                                 headers={'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                                          'Authorization': ('Basic %s' % bearer_token_64)},
                                 data={'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                                       'assertion': gen_jwt_token, }, )
        if response.status_code != 200:
            raise UserError(_(str(response.status_code) + ': ' + str(response.text)))
        try:
            token = response.json().get('token')
            _logger.info("Created SVF access token!")
        except requests.exceptions.HTTPError:
            raise UserError(_('SVF認証に失敗しました。 API キーとシークレットを確認してください。'))
        return token

    def svf_template_export_common(self, data, type_report):
        params = self.get_svf_param()
        specific_params = self.check_specific_param_config(type_report)
        token = self.get_access_token()

        # Hmm title japanese work in postman, but here not work
        #  oh postman can send with 202 response, but get somthing like è«æ±æ¸ 2022å¹´09æ22æ¥ in svfcloud :))
        # title_pdf = fields.Datetime.now().strftime("%Y年%m月%d日")
        # if type_report == 'R002':
        #     title_pdf = '請求書_' + title_pdf

        title_pdf = fields.Datetime.now().strftime("%Y%m%d")
        if type_report == 'R002':
            title_pdf = 'invoice_' + title_pdf

        data_key = 'data%2F' + title_pdf
        res = requests.post(
            url=params['svf_cloud_access_form_output_req_url'],
            headers={'Authorization': ('Bearer %s' % token)},
            files={
                # 'name': 'System Gear Test',
                'printer': 'PDF',
                'source': 'CSV',
                'defaultForm': specific_params['form_format_path'],
                data_key: ('test.csv', data.encode(), 'text/csv'),
                'redirect': 'false',
            }
        )

        if res.status_code == 202:
            # download pdf
            url_download = res.headers['Location']
            res_download = requests.get(
                url=url_download,
                headers={'Accept': 'application/octet-stream',
                         'Authorization': ('Bearer %s' % token)}, )
            self.cancel_access_token(token)
            if res_download.status_code != 200:
                raise UserError(str(res_download.status_code) + " : " + res_download.text)
            content_file_pdf = res_download.content
            vals = {
                'name': title_pdf + '.pdf',
                'datas': base64.b64encode(content_file_pdf).decode('utf-8'),
                'type': 'binary',
                'res_model': 'account.move',
                'res_id': self.id,
                'x_no_need_save': True,
            }
            file_pdf = self.env['ir.attachment'].create(vals)

            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/' + str(file_pdf.id) + '?download=true',
                'target': 'new',
            }

        elif res.status_code == 400:
            raise UserError('SVF Cloudへの	リクエスト内容が不正です。')
        if res.status_code == 401:
            raise UserError('SVF Cloudの認証情報が不正なです。')
        if res.status_code == 403:
            raise UserError('SVF Cloudの実行権限がないか、必要なポイントが足りていません。')
        if res.status_code == 429:
            raise UserError('SVF CloudのAPIコール数が閾値を超えました。')
        if res.status_code == 503:
            raise UserError('SVF Cloudの同時に処理できる数の制限を超過しました。しばらく時間を置いてから再度実行してください。')

        # End Region

    def cancel_access_token(self, token=False):
        param = self.get_svf_param()
        try:
            response = requests.post(url=urljoin(param['cloud_access_token_req_url'], 'oauth2/revoke'),
                                     headers={'Content-Type': 'application/x-www-form-urlencoded',
                                              'Authorization': ('Bearer %s' % token)},
                                     data={'token': token}, )
            _logger.info("Canceled svf access token!")
        except requests.exceptions.HTTPError:
            raise UserError(_('アクセストークンのキャンセルでエラーが発生しました。 %s') % response.text)
