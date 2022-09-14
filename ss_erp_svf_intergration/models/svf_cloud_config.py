# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import jwt
import datetime
import calendar
from base64 import urlsafe_b64encode, urlsafe_b64decode
import base64
import json
import ujson
import rsa

import hashlib
import hmac
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

        result = {
            'client_id': client_id,
            'cloud_secret': cloud_secret,
            'cloud_private_key': cloud_private_key,
            'cloud_user_id': cloud_user_id,
            'cloud_access_token_exp_sec': cloud_access_token_exp_sec,
            'cloud_access_token_req_url': cloud_access_token_req_url,
        }
        return result

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
        print('##########################', gen_jwt_token)

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
        except requests.exceptions.HTTPError:
            raise UserError(_('The SVF authentication failed. Please check your API key and secret.'))
        print('**************************', token)
        return token

    def cancel_access_token(self, token=False):
        param = self.get_svf_param()
        try:
            response = requests.post(url=urljoin(param['cloud_access_token_req_url'], 'oauth2/revoke'),
                                     headers={'Content-Type': 'application/x-www-form-urlencoded',
                                              'Authorization': ('Bearer %s' % token)},
                                     data={'token': token}, )
        except requests.exceptions.HTTPError:
            raise UserError(_('An error occurred when canceling the access token. %s') % response.text)