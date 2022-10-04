# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date, timedelta, datetime
from odoo.fields import Date, Datetime


class AccountReceivableList(models.TransientModel):
    _name = 'account.receivable.list'

    due_date_start = fields.Date(string='期日（開始）')
    due_date_end = fields.Date(string='期日（終了）')

    def svf_template_export(self):
        data_file = self._prepare_data_file()
        print(data_file)
        return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_file, type_report='R005')

    # 売掛金一覧表作成。
    def create_list_of_accounts_receivable(self):
        return self.svf_template_export()

    def _get_invoice_history(self):
        branch = self._get_branch_of_login_user()

        due_date_start = datetime.combine(self.due_date_start, datetime.min.time())
        due_date_end = datetime.combine(self.due_date_end, datetime.max.time())

        str_due_date_start = due_date_start.strftime("%Y年%m月%d日")
        str_due_date_end = due_date_end.strftime("%Y年%m月%d日")

        query = f''' 
            WITH previous_period_balance AS (
            SELECT
                tb1.partner_id,
                tb1.x_organization_id,
                SUM ( tb1.amount ) AS previous_month_balance
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
                        AND am.date < '{self.due_date_start}'
                        AND am.move_type IN ( 'out_invoice', 'out_refund' )
                        AND am.x_organization_id = '{branch.id}'
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
                        AND am.date < '{self.due_date_start}'
                        AND am.x_organization_id = '{branch.id}'
                    ) tb1 
            GROUP BY
                tb1.partner_id,
                tb1.x_organization_id 
            ), 
            this_period_money_collect AS (
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
            this_period_earning AS (
            SELECT
                tb3.partner_id,
                tb3.x_organization_id,
                sum(tb3.amount_untaxed) AS earnings,
                sum(tb3.amount_tax) AS consumption_tax
            FROM 
                (
                SELECT
                am.partner_id,
                am.x_organization_id,
                CASE WHEN am.move_type = 'out_invoice' THEN am.amount_untaxed ELSE -am.amount_untaxed END AS amount_untaxed, 
                CASE WHEN am.move_type = 'out_invoice' THEN am.amount_tax ELSE -am.amount_tax END AS amount_tax 
                FROM
                    account_move am
                WHERE
                        am.STATE = 'posted' 
                        AND am.move_type IN ( 'out_invoice', 'out_refund' ) 
                        AND am.date >= '{self.due_date_start}' and am.date <= '{self.due_date_end}'
                        AND am.x_organization_id = '{branch.id}'
                )tb3
            GROUP BY
                tb3.partner_id,
                tb3.x_organization_id 
            ), partner_contract_condition
            AS (
                SELECT 
                * FROM
                (SELECT 
                        tb5.partner_id,
                        tb5.x_organization_id,
                        sep.payment_term AS payment,
                        sep.receipt_type_branch AS conditions,
                        ROW_NUMBER() OVER(PARTITION BY tb5.partner_id,tb5.x_organization_id ORDER BY ID ASC) rownumber
                FROM
                    (SELECT
                        tb4.partner_id,
                        tb4.x_organization_id,		
                        sum(tb4.amount_total) AS total_invoice_amount
                    FROM 
                        (
                        SELECT
                        am.partner_id,
                        am.x_organization_id,
                        CASE WHEN am.move_type = 'out_invoice' THEN am.amount_total ELSE -am.amount_total END AS amount_total 
                        FROM
                            account_move am
                        WHERE
                                am.STATE = 'posted' 
                                AND am.move_type IN ( 'out_invoice', 'out_refund' ) 
                        )tb4
                    GROUP BY
                        tb4.partner_id,
                        tb4.x_organization_id 
                    ) tb5
                    LEFT JOIN 
                    ss_erp_partner_payment_term sep ON tb5.partner_id = sep.partner_id AND tb5.x_organization_id = sep.organization_id
                    WHERE (sep.range = 'up' AND tb5.total_invoice_amount > sep.total_amount) OR (sep.range = 'down' and tb5.total_invoice_amount < sep.total_amount)
                    AND tb5.x_organization_id = '{branch.id}'
                    ORDER BY tb5.partner_id, tb5.x_organization_id, sep.id) tb6
                    WHERE  rownumber = 1
            ), 
            last_payment_term AS (
            SELECT * FROM (
                SELECT 
                    partner_id
                    , x_organization_id
                    , invoice_payment_term_id,
                                    ROW_NUMBER() OVER(PARTITION BY partner_id, x_organization_id ORDER BY ID ASC) rownumber
                FROM account_move
                WHERE state = 'posted' and invoice_payment_term_id IS NOT NULL
                ORDER BY invoice_date desc) tb7 where rownumber = 1
            )            
            SELECT
            seo.organization_code AS branch_code
            ,seo.name AS branch_name
            ,concat('{str_due_date_start}','~','{str_due_date_end}') AS target_date
            ,to_char(now() AT TIME ZONE 'JST', 'YYYY年MM月DD日 HH24:MI:SS') AS output_date 
            ,rp.ref AS customer_code
            ,rp.name AS customer_name
            ,COALESCE (ppb.previous_month_balance,0) AS previous_month_balance
            ,0 AS correction
            ,COALESCE (tpmc.receipts,0) AS receipts
            ,COALESCE (ppb.previous_month_balance,0) - COALESCE (tpmc.receipts,0) AS carried_forward
            ,COALESCE (tpe.earnings,0) AS earnings
            ,COALESCE (consumption_tax,0) AS consumption_tax
            ,COALESCE (ppb.previous_month_balance,0) - COALESCE (tpmc.receipts,0) + COALESCE (tpe.earnings,0) + COALESCE (consumption_tax,0) AS this_month_balance
            ,tcc.payment
            ,tcc.conditions
            ,apt.name AS closing_date
            FROM this_period_earning tpe
            FULL OUTER JOIN previous_period_balance ppb ON tpe.partner_id = ppb.partner_id AND tpe.x_organization_id = ppb.x_organization_id
            LEFT JOIN ss_erp_organization seo ON tpe.x_organization_id = seo.id
            LEFT JOIN res_partner rp ON tpe.partner_id = rp.id
            LEFT JOIN this_period_money_collect tpmc ON tpe.partner_id = tpmc.partner_id AND tpe.x_organization_id = tpmc.x_organization_id
            LEFT JOIN partner_contract_condition tcc ON tpe.partner_id = tcc.partner_id AND tpe.x_organization_id = tcc.x_organization_id
            LEFT JOIN last_payment_term plt ON tpe.partner_id = plt.partner_id AND plt.x_organization_id = tcc.x_organization_id
            LEFT JOIN account_payment_term apt ON plt.invoice_payment_term_id = apt.id'''
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
            '"branch_code","branch_name","target_date","output_date","customer_code","customer_name",' + \
            '"previous_month_balance","correction","receipts","carried_forward","earnings","consumption_tax",' + \
            '"this_month_balance","payment","conditions","closing_date"']

        total = {'previous_month_balance': 0, 'correction': 0, 'receipts': 0, 'carried_forward': 0, 'earnings': 0,
                 'consumption_tax': 0, 'this_month_balance': 0}

        # データ＜詳細（取引先）＞
        invoice_history = self._get_invoice_history()

        if not invoice_history:
            raise UserError(_("出力対象のデータがありませんでした。"))

        for row in invoice_history:
            data_line = ""
            for col in row:
                if col in ["previous_month_balance", "correction", "receipts", "carried_forward", "earnings",
                           "consumption_tax", "this_month_balance"]:
                    if row[col] is not None:
                        data_line += '"' + "{:,}".format(int(row[col])) + '",'
                        total[col] += int(row[col])
                    else:
                        data_line += '"",'
                else:
                    if row[col] is not None:
                        data_line += '"' + str(row[col]) + '",'
                    else:
                        data_line += '"",'
            new_data.append(data_line)

        # データ＜合計＞
        total_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
            invoice_history[-1]['branch_code'],  # 支店コード
            invoice_history[-1]['branch_name'],  # 支店名
            invoice_history[-1]['target_date'],  # 対象年月
            invoice_history[-1]['output_date'],  # 出力日付
            '',  # 取引先コード
            '**  合　計　**',  # 取引先名称
            "{:,}".format(total['previous_month_balance']),
            "{:,}".format(total['correction']),
            "{:,}".format(total['receipts']),
            "{:,}".format(total['carried_forward']),
            "{:,}".format(total['earnings']),
            "{:,}".format(total['consumption_tax']),
            "{:,}".format(total['this_month_balance']),
            '',
            '',
            '',
        )
        new_data.append(total_line)
        # データ＜総合計＞
        total_total_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
            invoice_history[-1]['branch_code'],  # 支店コード
            invoice_history[-1]['branch_name'],  # 支店名
            invoice_history[-1]['target_date'],  # 対象年月
            invoice_history[-1]['output_date'],  # 出力日付
            '',  # 取引先コード
            '**  総合計　**',
            "{:,}".format(total['previous_month_balance']),
            "{:,}".format(total['correction']),
            "{:,}".format(total['receipts']),
            "{:,}".format(total['carried_forward']),
            "{:,}".format(total['earnings']),
            "{:,}".format(total['consumption_tax']),
            "{:,}".format(total['this_month_balance']),
            '',
            '',
            '',
        )

        new_data.append(total_total_line)
        return "\n".join(new_data)

