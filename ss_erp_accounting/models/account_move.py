# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_organization_id = fields.Many2one(
        'ss_erp.organization', string="担当組織", index=True, default=lambda self: self._get_default_x_organization_id())
    x_responsible_dept_id = fields.Many2one(
        'ss_erp.responsible.department', string="管轄部門", index=True, default=lambda self: self._get_default_x_responsible_dept_id())

    def _get_default_x_organization_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id.organization_first
        else:
            return False

    def _get_default_x_responsible_dept_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id and employee_id.department_jurisdiction_first:
            return employee_id.department_jurisdiction_first[0]
        else:
            return False

    x_responsible_user_id = fields.Many2one('res.users', string='業務担当')
    x_mkt_user_id = fields.Many2one('res.users', string='営業担当')
    x_is_fb_created = fields.Boolean(string='FB作成済みフラグ', store=True, default=False, copy=False)
    x_is_not_create_fb = fields.Boolean(string='FB対象外', store=True, index=True)

    x_receipt_type = fields.Selection(
        string='入金手段',
        selection=[
            ('bank', '振込'),
            ('transfer', '振替'),
            ('bills', '手形'),
            ('cash', '現金'),
            ('paycheck', '小切手'),
            ('branch_receipt', '他店入金'),
            ('offset', '相殺'), ],
        required=False, index=True, store=True)

    x_payment_type = fields.Selection(
        string='支払手段',
        selection=[('bank', '振込'),
                   ('cash', '現金'),
                   ('bills', '手形'), ],
        required=False, index=True, store=True)

    # @api.model
    # def create(self, vals):
    #     if 'move_type' in vals:
    #         if vals['move_type'] in ['in_invoice', 'in_refund']:
    #             head_office_organization = self.env['ss_erp.organization'].search([('organization_code', '=', '000')])
    #             organization = self.env['ss_erp.organization'].search([('organization_code', 'like', '00000')])
    #             if head_office_organization:
    #                 vals['x_organization_id'] = head_office_organization.id
    #                 business_department = self.env['ss_erp.responsible.department'].search([('name', '=', '業務')])
    #                 vals['x_responsible_dept_id'] = business_department.id
    #             elif organization:
    #                 vals['x_organization_id'] = organization.id
    #         elif vals.get('invoice_origin') and vals['move_type'] in ['out_invoice', 'out_refund']:
    #             sale_doc_reference = vals['invoice_origin'].split(', ')
    #             sale_reference = self.env['sale.order'].search([('name', 'in', sale_doc_reference)], limit=1)
    #             vals['x_organization_id'] = sale_reference.x_organization_id.id
    #             vals['x_responsible_dept_id'] = sale_reference.x_responsible_dept_id.id
    #
    #             # Todo reconfirm
    #             vals['x_responsible_user_id'] = sale_reference.user_id.id
    #             vals['x_mkt_user_id'] = sale_reference.user_id.id
    #         # vals['x_payment_method'] = self.x_payment_method
    #     res = super(AccountMove, self).create(vals)
    #     return res

    # @api.onchange('move_type')
    # def _onchange_type(self):
    #     ''' Onchange made to filter the partners depending of the type. '''
    #     res = super()._onchange_type()
    #     if self.move_type in ['in_invoice', 'in_refund']:
    #         head_office_organization = self.env['ss_erp.organization'].search([('organization_code', '=', '000')])
    #         self.x_organization_id = head_office_organization.id
    #         business_department = self.env['ss_erp.responsible.department'].search([('name', '=', '業務')])
    #         self.x_responsible_dept_id = business_department.id
    #     elif self.invoice_origin and self.move_type in ['out_invoice', 'out_refund']:
    #         sale_doc_reference = self.invoice_origin.split(', ')
    #         sale_reference = self.env['sale.order'].search([('name', 'in', sale_doc_reference)], limit=1)
    #         self.x_organization_id = sale_reference.x_organization_id.id
    #         self.x_responsible_dept_id = sale_reference.x_organization_id.id
    #
    #     return res

    def _move_autocomplete_invoice_lines_values(self):
        ''' This method recomputes dynamic lines on the current journal entry that include taxes, cash rounding
        and payment terms lines.
        '''
        self.ensure_one()

        for line in self.line_ids.filtered(lambda l: not l.display_type):
            analytic_account = line._cache.get('analytic_account_id')

            # Do something only on invoice lines.
            if line.exclude_from_invoice_tab:
                continue

            # Shortcut to load the demo data.
            # Doing line.account_id triggers a default_get(['account_id']) that could returns a result.
            # A section / note must not have an account_id set.
            if not line._cache.get('account_id') and not line._origin:
                line.account_id = line._get_computed_account() or self.journal_id.default_account_id

            line.x_sub_account_id = line.account_id.x_sub_account_ids[0] if line.account_id.x_sub_account_ids else False

            if line.product_id and not line._cache.get('name'):
                line.name = line._get_computed_name()

            # Compute the account before the partner_id
            # In case account_followup is installed
            # Setting the partner will get the account_id in cache
            # If the account_id is not in cache, it will trigger the default value
            # Which is wrong in some case
            # It's better to set the account_id before the partner_id
            # Ensure related fields are well copied.
            if line.partner_id != self.partner_id.commercial_partner_id:
                line.partner_id = self.partner_id.commercial_partner_id
            line.date = self.date
            line.recompute_tax_line = True
            line.currency_id = self.currency_id
            if analytic_account:
                line.analytic_account_id = analytic_account

        self.line_ids._onchange_price_subtotal()
        self._recompute_dynamic_lines(recompute_all_taxes=True)

        values = self._convert_to_write(self._cache)
        values.pop('invoice_line_ids', None)
        return values
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


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_sub_account_id = fields.Many2one('ss_erp.account.subaccount', string='補助科目')

    x_organization_id = fields.Many2one('ss_erp.organization', related='move_id.x_organization_id')
    x_responsible_dept_id = fields.Many2one('ss_erp.responsible.department', related='move_id.x_responsible_dept_id')
