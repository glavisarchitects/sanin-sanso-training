# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json
from datetime import date, timedelta
from odoo.fields import Date, Datetime


class AccountReceivableBalanceConfirm(models.TransientModel):
    _name = 'account.receivable.balance.confirm'

    return_date = fields.Date(string='返送日')
    close_date = fields.Date(string='締日')
    partner_id = fields.Many2one('res.partner', string='得意先顧客')

    # form/Sample/ga_test/
    def svf_template_export(self):
        data_file = self._prepare_data_file()
        return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_file, type_report='R003')

    # def _get_data_svf_r003(self):
    #     query = f''' SELECT
    #                         zip,
    #                         CONCAT(rcs.name, ' ', rp.street, ' ', rp.street2) address,
    #                         rp.name customer_name,
    #                         CONCAT(zip, rp.street, rp.street2) customer_barcode,
    #                         '保護シールをはがし、当社残高を御確認ください。' message1,
    #                         '{self.close_date.strftime("%Y年%m月%d日")}' closing_date1,
    #                         '山陰酸素工業（株）売掛金残高（消費税含む）' message2,
    #                         (SELECT CASE When SUM(amount_total) is NUll then 0 ELSE SUM(amount_total) END period_amount_total
    #                         from account_move
    #                         WHERE partner_id = '{self.partner_id.id}' AND move_type = 'out_invoice'
    #                          AND invoice_date BETWEEN '{self.return_date}' and '{self.close_date}'
    #                          AND state = 'posted' and payment_state = 'not_paid')
    #                         +
    #                         (SELECT  CASE When SUM(amount) is NUll then 0 ELSE SUM(amount) END payment_amount_total from account_payment ap
    #                         left join account_move jour_am ON jour_am.id = ap.move_id
    #                         WHERE ap.partner_id = '{self.partner_id.id}' AND
    #                         ap.payment_type = 'inbound' and ap.x_receipt_type = 'bills' and jour_am.state = 'posted') total,
    #                         '{self.return_date.strftime("%Y年%m月%d日")}' return_date,
    #                         CONCAT('担当支店：', seo.name) branch,
    #                         CONCAT('TEL：', seo.organization_phone) branch_phone_number,
    #                         -- '※　尚、本書は貴社に対する支払の請求および督促ではございません。あくまでも締日の月+"月末現在の残高の確認となります。ご了承下さい。' supplement,
    #                         -- '山陰酸素工業株式会社内　
    #                         --　　　　山根朋洋会計事務所　殿　
    #                         --　　　　
    #                         --　　　当社の山陰酸素工業に対する債務額は
    #                         --　　　下記のとおり相違いないことを確認いたします。' message3,
    #                         '{self.close_date.strftime("%Y年%m月%d日")}' closing_date2,
    #                         rp.ref customer_code,
    #                         '' tablexxx,
    #                         '残高確認書' title
    #
    #                         FROM account_move am
    #                         LEFT Join res_partner rp ON am.partner_id = rp.id
    #                         LEFT Join res_country_state rcs ON rp.state_id = rcs.id
    #                         LEFT Join ss_erp_organization seo ON am.x_organization_id = seo.id
    #
    #                         WHERE am.partner_id = '{self.partner_id.id}' AND 	am.invoice_date BETWEEN '{self.return_date}' and '{self.close_date}' LIMIT 1
    #                     ;'''
    #     self.env.cr.execute(query)
    #     return self.env.cr.dictfetchall()

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
        query = ''' 
            WITH balance AS (
            SELECT
                tb1.partner_id,
                sum( tb1.amount_total ) AS total 
            FROM
                (
            SELECT
                partner_id,
                amount_total 
            FROM
                account_move 
            WHERE
                move_type = 'out_invoice' 
                AND invoice_date <= '%s' 
                AND state = 'posted' UNION ALL
            SELECT
                ap.partner_id,
                ap.amount 
            FROM
                account_payment ap
                LEFT JOIN account_move am ON ap.move_id = am.id 
            WHERE
                ap.payment_type = 'inbound' 
                AND ap.x_receipt_type = 'bills' 
                AND am.state = 'posted' 
                AND am.date <= '%s' 
                ) AS tb1 
            GROUP BY
                tb1.partner_id 
                ) 
            SELECT
                ba.partner_id,
                concat(rp.name,'様') as customer_name,
                rp.zip,
                rp.ref as customer_code,
                concat(rcs.name,rp.city,rp.street,rp.street2) as address
                ba.total 
            FROM
                balance ba
                LEFT JOIN res_partner rp ON ba.partner_id = rp.id
                LEFT JOIN res_country_state rcs ON rp.state_id = rcs.id
                where ba.partner_id = '%s'        
            ''' % (self.close_date, self.close_date, self.partner_id.id)
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def _convert_customer_barcode(self, street=None, street2=None):
        str = ''
        if street is not None:
            str += street
        if street2 is not None:
            str += street2

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

        str = new_str
        if str[0] == '-':
            str = str[1:]

        if str[-1] == '-':
            str = str[:-1]
        return str

    def _prepare_data_file(self):
        # ヘッダ
        new_data = [
            '"zip","address","customer_name","customer_barcode","closing_date1","total",' + \
            '"return_date","branch","branch_phone_number","closing_date2","customer_code"']

        branch = self._get_branch_of_login_user()

        close_date = '%s年%s月%s日 現在' % (self.close_date.year, self.close_date.month, self.close_date.day)
        phone = "TEL：%s" % (branch.organization_phone if branch.organization_phone else '')

        rec = self._get_accounts_receivable()
        if len(rec) > 0:
            data_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
                rec[0]['zip'],
                rec[0]['address'],
                rec[0]['customer_name'],
                rec[0]['zip'] + '-' + self._convert_customer_barcode(street=rec[0]['street'],
                                                                     street2=rec[0]['street2']),
                close_date,
                "￥" + "{:,}".format(int(rec[0]['total'])),
                self.return_date,
                "担当支店：" + branch.name,
                phone,
                close_date,
                rec[0]['customer_code']
            )
            new_data.append(data_line)
        return "\n".join(new_data)
