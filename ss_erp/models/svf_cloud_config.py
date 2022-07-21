# -*- coding: utf-8 -*-
from odoo import models, fields, api
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
        request_header = base64.b64encode((param['client_id'] + ':' + param['cloud_secret']).encode('utf-8'))
        x = base64.b64encode('.'.encode('utf-8'))
        headers_64 = base64.b64encode(ujson.dumps(headers).encode('utf-8'))
        payload_64 = base64.b64encode(ujson.dumps(payload).encode('utf-8'))
        sign_data = headers_64 + base64.b64encode('.'.encode('utf-8')) + payload_64
        # private_key = rsa.PrivateKey(param['cloud_private_key'])
        secret_key = base64.b64encode(param['cloud_private_key'].encode('utf-8'))
        # signature = base64.b64encode(rsa.sign(sign_data, param['cloud_private_key'], 'SHA-256'))
        signature = hmac.new(secret_key, sign_data, hashlib.sha256).hexdigest()
        # signature = base64.b64encode(rsa.sign(sign_data, param['cloud_private_key'], 'SHA-256'))
        # beatoken = headers_64 + payload_64 + signature
        _logger.info("signatureSS: ", signature)
        return signature
