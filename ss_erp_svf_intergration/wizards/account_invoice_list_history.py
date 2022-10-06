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

        str_due_date_start = self.due_date_start.strftime("%Y年%m月%d日")
        str_due_date_end = self.due_date_end.strftime("%Y年%m月%d日")

        branch = self._get_branch_of_login_user()

        query = f''' WITH previous_month_invoice AS (
                SELECT
                    tb1.partner_id,
                    tb1.x_organization_id,
                    SUM ( tb1.amount ) AS previous_month_amount
                FROM
                (
                        SELECT
                            am.partner_id,
                            am.x_organization_id,
                            CASE WHEN am.move_type = 'out_invoice' THEN am.amount_total ELSE -am.amount_total END AS amount 
                        FROM
                        account_move am 
                        WHERE
                        am.STATE = 'posted' 
                        AND am.move_type IN ( 'out_invoice', 'out_refund' )
                        AND am.x_organization_id = '{branch.id}'
                        AND am.date >= '{start_day_of_prev_month}' 
                        AND am.date <= '{last_day_of_prev_month}' 
                        UNION ALL
                            SELECT
                            ap.partner_id,
                            ap.x_organization_id,
                            CASE WHEN ap.payment_type = 'inbound' THEN- ap.amount ELSE ap.amount END 
                        FROM
                        account_payment ap
                        LEFT JOIN account_move am ON ap.move_id = am.ID 
                        WHERE
                        ap.payment_type IN ( 'inbound', 'outbound' ) 
                        AND ap.move_id IS NOT NULL
                        AND am.date >= '{start_day_of_prev_month}' 
                        AND am.date <= '{last_day_of_prev_month}' 		
                        AND am.x_organization_id = '{branch.id}'
                        ) tb1 
                        GROUP BY
                                tb1.partner_id,
                                tb1.x_organization_id 
                ),
                this_month_money_collect AS (
                SELECT
                        tb2.partner_id,
                        tb2.x_organization_id,
                        sum(tb2.amount) AS receipts
                FROM 
                        (
                        SELECT
                        ap.partner_id,
                        ap.x_organization_id,
                        CASE WHEN ap.payment_type = 'inbound' THEN ap.amount ELSE -ap.amount END AS amount
                        FROM
                                account_payment ap
                                LEFT JOIN account_move am ON ap.move_id = am.ID 
                        WHERE
                                ap.payment_type IN ( 'inbound', 'outbound' ) 
                                AND ap.move_id IS NOT NULL 
                                AND ap.partner_id IS NOT NULL
                                AND am.date >= '{self.due_date_start}' and am.date <= '{self.due_date_end}'
                                AND am.x_organization_id = '{branch.id}'
                        )tb2
                GROUP BY
                        tb2.partner_id,
                        tb2.x_organization_id 
                ),
                previous_month_balance AS (
                SELECT
                    tb3.partner_id,
                    tb3.x_organization_id,
                    SUM ( tb3.amount_residual ) AS previous_month_balance
                FROM
                (
                        SELECT
                            am.partner_id,
                            am.x_organization_id,
                            CASE WHEN am.move_type = 'out_invoice' THEN am.amount_residual ELSE -am.amount_residual END AS amount_residual 
                        FROM
                        account_move am 
                        WHERE
                        am.STATE = 'posted' 
                        AND am.move_type IN ( 'out_invoice', 'out_refund' )
                        AND am.x_organization_id = '{branch.id}'
                        AND am.date >= '{start_day_of_prev_month}' 
                        AND am.date <= '{last_day_of_prev_month}' 
                        ) tb3 
                        GROUP BY
                                tb3.partner_id,
                                tb3.x_organization_id 
                ),
                this_month_earning AS (
                SELECT
                        tb4.partner_id,
                        tb4.x_organization_id,
                        sum(tb4.amount_untaxed) AS this_month_earnings,
                        sum(tb4.amount_tax) AS consumption_tax,
                        sum(tb4.amount_total) AS this_month_amount 
                FROM 
                        (
                        SELECT
                        am.partner_id,
                        am.x_organization_id,
                        CASE WHEN am.move_type = 'out_invoice' THEN am.amount_untaxed ELSE -am.amount_untaxed END AS amount_untaxed, 
                        CASE WHEN am.move_type = 'out_invoice' THEN am.amount_tax ELSE -am.amount_tax END AS amount_tax, 
                        CASE WHEN am.move_type = 'out_invoice' THEN am.amount_total ELSE -am.amount_total END AS amount_total 
                        FROM
                                account_move am
                        WHERE
                                        am.STATE = 'posted' 
                                        AND am.move_type IN ( 'out_invoice', 'out_refund' ) 
                                        AND am.date >= '{self.due_date_start}' and am.date <= '{self.due_date_end}'
                                        AND am.x_organization_id = '{branch.id}'
                        )tb4
                GROUP BY
                        tb4.partner_id,
                        tb4.x_organization_id 
                )
                SELECT
                    seo.organization_code AS branch_code
                    ,seo.name AS branch_name
                    ,concat('{str_due_date_start}','~','{str_due_date_end}') AS target_date
                    ,to_char(now() AT TIME ZONE 'JST', 'YYYY年MM月DD日 HH24:MI:SS') as output_date
                    ,rp.ref AS customer_code
                    ,rp.name AS customer_name
                    ,COALESCE (pmi.previous_month_amount,0) AS previous_month_amount
                    ,COALESCE (tmmc.receipts,0) AS receipts
                    ,COALESCE (pmb.previous_month_balance,0) AS previous_month_balance
                    ,COALESCE (tme.this_month_earnings,0) AS this_month_earnings
                    ,COALESCE (tme.consumption_tax,0) AS consumption_tax
                    ,COALESCE (tme.this_month_amount,0) AS this_month_amount
                FROM this_month_earning tme
                LEFT JOIN previous_month_invoice pmi ON tme.partner_id = pmi.partner_id
                LEFT JOIN this_month_money_collect tmmc ON tme.partner_id = tmmc.partner_id
                LEFT JOIN previous_month_balance pmb ON tme.partner_id = pmb.partner_id
                LEFT JOIN ss_erp_organization seo ON tme.x_organization_id = seo.id
                LEFT JOIN res_partner rp ON tme.partner_id = rp.id
                WHERE rp.x_is_customer = 't'
                '''
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

        total = {'previous_month_amount': 0, 'receipts': 0, 'previous_month_balance': 0, 'this_month_earnings': 0, 'consumption_tax': 0,
                 'this_month_amount': 0}
        # データ＜詳細（取引先）＞
        invoice_history = self._get_invoice_history()

        if not invoice_history:
            raise UserError(_("出力対象のデータがありませんでした。"))

        for row in invoice_history:
            data_line = ""
            for col in row:
                if col in ["previous_month_amount", "receipts", "previous_month_balance", "this_month_earnings",
                           "consumption_tax", "this_month_amount"]:
                    if row[col] is not None:
                        data_line += '"' + "{:,}".format(int(row[col])) + '",'
                        total[col] += int(row[col])
                    else:
                        data_line += '"0",'
                else:
                    if row[col] is not None:
                        data_line += '"' + str(row[col]) + '",'
                    else:
                        data_line += '"",'
            new_data.append(data_line)

        # データ＜合計＞
        total_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
            invoice_history[-1]['branch_code'],  # 支店コード
            invoice_history[-1]['branch_name'],  # 支店名
            invoice_history[-1]['target_date'],  # 対象年月
            invoice_history[-1]['output_date'],  # 出力日付
            '',  # 取引先コード
            '**  合　計　**',  # 取引先名称
            "{:,}".format(total['previous_month_amount']),
            "{:,}".format(total['receipts']),
            "{:,}".format(total['previous_month_balance']),
            "{:,}".format(total['this_month_earnings']),
            "{:,}".format(total['consumption_tax']),
            "{:,}".format(total['this_month_amount']),
        )
        new_data.append(total_line)
        # データ＜総合計＞
        total_total_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
            invoice_history[-1]['branch_code'],  # 支店コード
            invoice_history[-1]['branch_name'],  # 支店名
            invoice_history[-1]['target_date'],  # 対象年月
            invoice_history[-1]['output_date'],  # 出力日付
            '',
            '**  総合計　**',
            "{:,}".format(total['previous_month_amount']),
            "{:,}".format(total['receipts']),
            "{:,}".format(total['previous_month_balance']),
            "{:,}".format(total['this_month_earnings']),
            "{:,}".format(total['consumption_tax']),
            "{:,}".format(total['this_month_amount']),
        )
        new_data.append(total_total_line)
        return "\n".join(new_data)
