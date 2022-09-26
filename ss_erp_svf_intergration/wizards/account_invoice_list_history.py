# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date, timedelta
from odoo.fields import Date, Datetime
import pytz
import requests
import json


class AccountInvoiceListHistory(models.TransientModel):
    _name = 'account.invoice.list.history'

    due_date_start = fields.Date(string='期日（開始）')
    due_date_end = fields.Date(string='期日（終了）')

    def svf_template_export(self):
        data_file = self._prepare_data_file()
        print(data_file)
        return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_file, type_report='R006')

    # 請求書一覧表出力ボタンを追加する。
    def export_invoice_list_history(self):
        return self.svf_template_export()

    def _get_invoice_history(self, branch=None):
        last_day_of_prev_month = self.due_date_start.replace(day=1) - timedelta(days=1)
        start_day_of_prev_month = self.due_date_start.replace(day=1) - timedelta(days=last_day_of_prev_month.day)

        branch = self._get_branch_of_login_user()

        query = ''' SELECT
                rp.ref,
                rp.display_name,
                tb1.previous_month_amount,
                tb3.receipts,
                tb1.previous_month_balance,
                tb2.this_month_earnings,
                tb2.consumption_tax,
                tb2.this_month_amount 
                FROM
                -- 当月情報 
                ( 
                    SELECT
                    partner_id,
                    sum( amount_untaxed ) AS this_month_earnings,
                    sum( amount_tax ) AS consumption_tax,
                    sum( amount_total ) AS this_month_amount 
                FROM
                    account_move 
                WHERE
                    state = 'posted' and invoice_date <= '%s' and invoice_date >= '%s' and x_organization_id = '%s'
                GROUP BY
                    partner_id 
                    ) tb2
                    LEFT JOIN res_partner rp ON tb2.partner_id = rp.id
                    LEFT JOIN (-- 前月情報
                SELECT
                    partner_id,
                    sum( amount_total ) AS previous_month_amount,
                    sum( amount_residual ) AS previous_month_balance 
                FROM
                    account_move 
                WHERE
                    state = 'posted' and invoice_date < '%s' and invoice_date >= '%s' and x_organization_id = '%s'
                GROUP BY
                    partner_id 
                    ) tb1 ON rp.id = tb1.partner_id
                    LEFT JOIN 
                    ( -- 当月入金額
                    SELECT 
                        am.partner_id, 
                        sum( aml.debit ) as receipts 
                    FROM account_move_line aml
                    LEFT JOIN account_move am on aml.move_id = am.id
                    WHERE am.partner_id IS NOT NULL AND aml.payment_id IS NOT NULL and aml.date <= '%s' and aml.date >= '%s' and am.x_organization_id = '%s'
                    GROUP BY am.partner_id
                    ) tb3 ON tb3.partner_id = rp.id
                ORDER BY
                    rp.ref,
                    rp.display_name ''' % (
                    Date.to_date(self.due_date_end), Date.to_date(self.due_date_start), branch.id,
                    Date.to_date(self.due_date_start), Date.to_date(start_day_of_prev_month), branch.id,
                    Date.to_date(self.due_date_end), Date.to_date(self.due_date_start), branch.id)
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def _get_branch_of_login_user(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id.organization_first
        else:
            return False

    def _prepare_data_file(self):
        # ヘッダ
        new_data = [
            '"branch_code","branch_name","target_date","output_date","customer_code",' + \
            '"customer_name","previous_month_amount","receipts","previous_month_balance"' + \
            ',"this_month_earnings","consumption_tax","this_month_amount"']

        branch = self._get_branch_of_login_user()
        target_date = "%s ~ %s" % (self.due_date_start, self.due_date_end)
        datetime_now = Datetime.now() + timedelta(hours=9)

        total_previous_month_amount = 0
        total_receipts = 0
        total_previous_month_balance = 0
        total_this_month_earnings = 0
        total_consumption_tax = 0
        total_this_month_amount = 0

        # データ＜詳細（取引先）＞
        invoice_history = self._get_invoice_history()
        for row in invoice_history:
            data_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
                branch.organization_code,  # 支店コード
                branch.name,  # 支店名
                target_date,  # 対象年月
                str(datetime_now),  # 出力日付
                "" if row['ref'] is None else row['ref'],  # 取引先コード
                row['display_name'],  # 取引先名称
                0 if row['previous_month_amount'] is None else "{:,}".format(int(row['previous_month_amount'])),
                0 if row['receipts'] is None else "{:,}".format(int(row['receipts'])),
                0 if row['previous_month_balance'] is None else "{:,}".format(int(row['previous_month_balance'])),
                0 if row['this_month_earnings'] is None else "{:,}".format(int(row['this_month_earnings'])),
                0 if row['consumption_tax'] is None else "{:,}".format(int(row['consumption_tax'])),
                0 if row['this_month_amount'] is None else "{:,}".format(int(row['this_month_amount'])),
            )

            total_previous_month_amount += int(
                0 if row['previous_month_amount'] is None else row['previous_month_amount'])
            total_receipts += int(0 if row['receipts'] is None else row['receipts'])
            total_previous_month_balance += int(
                0 if row['previous_month_balance'] is None else row['previous_month_balance'])
            total_this_month_earnings += int(0 if row['this_month_earnings'] is None else row['this_month_earnings'])
            total_consumption_tax += int(0 if row['consumption_tax'] is None else row['consumption_tax'])
            total_this_month_amount += int(0 if row['this_month_amount'] is None else row['this_month_amount'])
            new_data.append(data_line)

        # データ＜合計＞
        total_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
            branch.organization_code,  # 支店コード
            branch.name,  # 支店名
            target_date,  # 対象年月
            str(datetime_now),  # 出力日付
            '',  # 取引先コード
            '**  合　計　**',  # 取引先名称
            "{:,}".format(total_previous_month_amount),
            "{:,}".format(total_receipts),
            "{:,}".format(total_previous_month_balance),
            "{:,}".format(total_this_month_earnings),
            "{:,}".format(total_consumption_tax),
            "{:,}".format(total_this_month_amount),
        )
        new_data.append(total_line)
        # データ＜総合計＞
        total_total_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
            branch.organization_code,  # 支店コード
            branch.name,  # 支店名
            target_date,  # 対象年月
            str(datetime_now),  # 出力日付
            '',
            '**  総合計　**',
            "{:,}".format(total_previous_month_amount),
            "{:,}".format(total_receipts),
            "{:,}".format(total_previous_month_balance),
            "{:,}".format(total_this_month_earnings),
            "{:,}".format(total_consumption_tax),
            "{:,}".format(total_this_month_amount),
        )
        new_data.append(total_total_line)
        return "\n".join(new_data)
