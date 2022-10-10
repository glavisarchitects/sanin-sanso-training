# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json
from datetime import date, timedelta, datetime
from odoo.fields import Date, Datetime


def _convert_customer_barcode(customer_barcode):

    str = customer_barcode
    if len(str)==0:
        return ''

    # 文字列内のアルファベットの小文字を大文字に置き換える。

    str = str.upper().replace('&', '').replace('/', '').replace('・', '').replace('.', '')
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    numbers = '0123456789'
    compare_string = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ-0123456789'

    new_str = ''
    len_str = len(str)
    for i, v in enumerate(str):
        if v not in compare_string:
            new_str += '-'
        else:
            if v == '-' or v in numbers:
                new_str += v
            else:
                if (str[i - 1] not in alphabet and i != 0) and (i < len_str - 1 and str[i + 1] not in alphabet):
                    new_str += v

    str = new_str

    last_char = ''
    new_str = ''
    for x in str:
        if x == '-' and last_char == '-':
            continue
        else:
            last_char = x
            new_str += x

    if len(str)!=0:
        str = new_str
        if str[0] == '-':
            str = str[1:]

    if len(str)!=0 and str[-1] == '-':
        str = str[:-1]
    return str


class AccountReceivableBalanceConfirm(models.TransientModel):
    _name = 'account.receivable.balance.confirm'

    return_date = fields.Date(string='返送日')
    close_date = fields.Date(string='締日')
    partner_id = fields.Many2one('res.partner', string='得意先顧客', domain="[('x_is_customer', '=', True)]")

    # form/Sample/ga_test/
    def svf_template_export(self):
        data_file = self._prepare_data_file()
        return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_file, type_report='R003')

    def _get_branch_of_login_user(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id.organization_first
        else:
            return False

    def receivable_balance_confirm(self):
        # self.check_param_config()
        # TODO: Recheck token return from svf.cloud.config
        # this is just sample code, need to redo when official information about SVF API is available
        return self.svf_template_export()

    def _get_accounts_receivable(self):
        close_date = datetime.combine(self.close_date, datetime.min.time()).strftime("%Y年%m月%d日")
        return_date = datetime.combine(self.return_date, datetime.min.time()).strftime("%Y年%m月%d日")
        query = f''' 
            WITH balance AS (
            SELECT
                tb1.partner_id,
                tb1.x_organization_id,
                sum( tb1.amount_total ) AS total 
            FROM
                (
            SELECT
                partner_id,
                x_organization_id,
                amount_total 
            FROM
                account_move 
            WHERE
                move_type = 'out_invoice' 
                AND invoice_date <= '{self.close_date}' 
                AND state = 'posted' UNION ALL
            SELECT
                ap.partner_id,
                ap.x_organization_id,
                ap.amount 
            FROM
                account_payment ap
                LEFT JOIN account_move am ON ap.move_id = am.id 
            WHERE
                ap.payment_type = 'inbound' 
                AND ap.x_receipt_type = 'bills' 
                AND am.state = 'posted' 
                AND am.date <= '{self.close_date}' 
                ) AS tb1 
            GROUP BY
                tb1.partner_id, tb1.x_organization_id
                ) 
            SELECT
                rp.zip,
                concat(rcs.name,rp.city,rp.street,rp.street2) as address,
                concat(rp.name,'様') as customer_name,
                concat(rp.zip,rp.street,rp.street2) as customer_barcode,
                concat('{close_date}','　現在') as closing_date1,
                ba.total,
                concat('【返送期限：','{return_date}','】') as return_date,
                concat('担当支店：',seo.name) as branch,
                concat('TEL:',seo.organization_phone) as branch_phone_number,
                concat('{close_date}','　現在') as closing_date2,
                rp.ref as customer_code                
            FROM
                balance ba
                LEFT JOIN res_partner rp ON ba.partner_id = rp.id
                LEFT JOIN res_country_state rcs ON rp.state_id = rcs.id
                LEFT JOIN ss_erp_organization seo on seo.id = ba.x_organization_id
                where ba.partner_id = '{self.partner_id.id}'        
            '''
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def _prepare_data_file(self):
        # ヘッダ
        new_data = [
            '"zip","address","customer_name","customer_barcode","closing_date1","total",' + \
            '"return_date","branch","branch_phone_number","closing_date2","customer_code"']

        recs = self._get_accounts_receivable()

        if not recs:
            raise UserError(_("出力対象のデータがありませんでした。"))

        if len(recs) > 0:
            for row in recs:
                data_line = ""
                for col in row:
                    if row[col] is not None:
                        if col == 'total':
                            data_line += '"￥' + "{:,}".format(int(row[col])) + '",'
                        else:
                            if col == 'customer_barcode':
                                data_line += '"' + _convert_customer_barcode(customer_barcode=row[col]) + '",'
                            else:
                                data_line += '"' + str(row[col]) + '",'

                    else:
                        data_line += '"",'

            new_data.append(data_line)
        return "\n".join(new_data)
