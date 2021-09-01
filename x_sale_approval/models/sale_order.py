# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError

class ErrorMessages:
    msg_01 = '必須項目を入力してください　 & 1'
    msg_02 = '配送情報 & 1'
    msg_03 = 'と明細 & 2'
    msg_04 = 'の整合性がありません'
    msg_05 = '申請期日は本日よりも後にしてください'
    msg_06 = '「承認」「否認」「差し戻し」のいずれかを選択してください'
    msg_07 = '「否認」「差し戻し」の場合は、理由を入力してください'
    msg_08 = '納期は現在より過去の日付は設定できません'
    msg_09 = '納期が設定されていません'
    msg_10 = '申請前に見積伝票を保存してください'

class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "x.x_company_organization.org_mixin"]

    # Approval
    crm_team_id = fields.Many2one("crm.team", string="申請先", required=True, help='crm_team_id')
    x_deadline = fields.Date(string='承認希望日', required=False, default=fields.Date.today, help='x_deadline')
    x_remark = fields.Char(string='備考', required=False, help='x_remark')
    x_reason = fields.Char(string='理由', required=False, help='x_reason')
    x_state = fields.Selection(string='判断', selection=[('approved', 'Approved'), ('reject', 'Reject'), ('cancel', 'Cancel'), ], required=False, help='x_state')
    x_sale_quotation_state = fields.Selection(string='判断',
                                              selection=[('temporary', 'Temporary'),
                                                         ('storage', 'Storage'),
                                                         ('approval', 'Approval'),
                                                         ('denied', 'Denied'),
                                                         ('quotation', 'Quotation'),
                                                         ('submitted', 'Submitted')],
                                              required=False,
                                              help='x_sale_quotation_state')


    def x_request_quotation_approval(self):
        self.ensure_one()
        raise ValidationError(_('action request quotation approval'))

    def x_approval_quotation(self):
        self.ensure_one()
        raise ValidationError(_('action approval quotation'))


    def write(self, vals):

        if self.x_sale_quotation_state == 'denied' and vals.get('x_sale_quotation_state') == 'approval':
            raise ValidationError('Error change denied to approval ')
        res = super(SaleOrder, self).write(vals)
        return res