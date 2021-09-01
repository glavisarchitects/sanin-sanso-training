# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError


class SettingRequest(models.Model):
    """
    model request create new partner
    """
    _name = "x.res.partner.newrequest"
    _description = 'Setting Request'

    state = fields.Selection([
        ('draft', 'ドラフト'),
        ('employee_send', '1次承認待ち'),
        ('branch_manager_approval', '2次承認待ち'),
        ('sale_head_approval', '3次承認待ち'),
        ('account_head_approval', '承認済み'),
    ], required=True, readonly=True, default='draft')
    name = fields.Char(default='新規', readonly=True)
    app_classification = fields.Selection([('new', '新規'), ('update', '更新'), ('branch_info', '支店の販売・購買情報')],
                                          default='new', string='申請区分')
