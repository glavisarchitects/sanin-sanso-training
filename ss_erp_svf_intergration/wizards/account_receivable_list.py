# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date, timedelta
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

        query = ''' 
                    SELECT
                        rp.ref,
                        rp.display_name,
                        tb2.previous_month_balance,
                        tb3.receipts,
                        tb2.previous_month_balance-tb3.receipts as carried_forward,
                        tb4.earnings,
                        tb4.consumption_tax,
                        tb2.previous_month_balance-tb3.receipts + tb4.earnings + tb4.consumption_tax as this_month_balance
                    FROM
                    (
                    SELECT
                        tb1.partner_id,
                        sum( tb1.amount_total ) AS previous_month_balance 
                    FROM
                    (-- 前月の請求書一覧 Sub-query1
                        SELECT
                            am.partner_id,
                        CASE
                            
                            WHEN am.move_type = 'out_invoice' THEN
                            am.amount_total ELSE ( - am.amount_total ) 
                            END AS amount_total 
                        FROM
                            account_move am 
                        WHERE
                            am.state = 'posted' 
                            AND am.x_organization_id = '%s' 
                            AND am.move_type IN ( 'out_invoice', 'out_refund' ) 
                            AND am.invoice_date < '%s' 
                        UNION ALL-- 前月までの支払
                        SELECT
                            aml.partner_id,
                            - sum( aml.debit ) 
                        FROM
                            account_move_line aml
                            LEFT JOIN account_move am ON aml.move_id = am.id 
                        WHERE
                            am.partner_id IS NOT NULL 
                            AND aml.payment_id IS NOT NULL 
                            AND am.x_organization_id = '%s' 
                            AND aml.date < '%s'                             
                        GROUP BY
                            aml.partner_id 
                            ) tb1 
                        GROUP BY
                            tb1.partner_id 
                            ) tb2
                    LEFT JOIN res_partner rp ON tb2.partner_id = rp.id
                    LEFT JOIN ( -- Sub-query2
                            SELECT
                                am.partner_id,
                                sum( aml.debit ) AS receipts 
                            FROM
                                account_move_line aml
                                LEFT JOIN account_move am ON aml.move_id = am.id 
                            WHERE
                                aml.partner_id IS NOT NULL 
                                AND aml.payment_id IS NOT NULL 
                                AND aml.date <= '%s' AND aml.date >= '%s' 
                                AND am.x_organization_id = '%s' 
                            GROUP BY
                            am.partner_id 
                        ) tb3 ON tb3.partner_id = rp.id
                    LEFT JOIN ( -- Sub-query3
                        SELECT
                        partner_id,
                        sum( amount_untaxed ) AS earnings,
                        sum( amount_tax ) AS consumption_tax
                        FROM
                        account_move 
                        WHERE
                        state = 'posted' and invoice_date <= '%s' and invoice_date >= '%s' and x_organization_id = '%s'
                        GROUP BY
                        partner_id 
                        ) tb4 on tb4.partner_id = rp.id
                    ORDER BY
                        rp.ref,
                    rp.display_name ''' % (branch.id, self.due_date_start, branch.id, self.due_date_start,  # Sub-query1
                                           self.due_date_end, self.due_date_start, branch.id,  # Sbu Query 2
                                           self.due_date_end, self.due_date_start, branch.id)  # Sbu Query 3
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
            '"previous_month_balance", "correction", "receipts", "carried_forward", "earnings", "consumption_tax",' + \
            '"this_month_balance", "payment", "conditions", "closing_date"']

        branch = self._get_branch_of_login_user()
        target_date = "%s ~ %s" % (self.due_date_start, self.due_date_end)
        output_date = Datetime.now() + timedelta(hours=9)

        total_previous_month_balance = 0
        total_correction = 0
        total_receipts = 0
        total_carried_forward = 0
        total_earnings = 0
        total_consumption_tax = 0
        total_this_month_balance = 0

        # データ＜詳細（取引先）＞
        invoice_history = self._get_invoice_history()
        for row in invoice_history:
            data_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
                branch.organization_code,  # 支店コード
                branch.name,  # 支店名
                target_date,  # 対象年月
                output_date,  # 出力日付
                "" if row['ref'] is None else row['ref'],  # 取引先コード
                row['display_name'],  # 取引先名称
                0 if row['previous_month_balance'] is None else "{:,}".format(row['previous_month_balance']),
                0, # correction
                0 if row['receipts'] is None else "{:,}".format(row['receipts']),
                0 if row['carried_forward'] is None else "{:,}".format(row['carried_forward']),
                0 if row['earnings'] is None else "{:,}".format(row['earnings']),
                0 if row['consumption_tax'] is None else "{:,}".format(row['consumption_tax']),
                0 if row['this_month_balance'] is None else "{:,}".format(row['this_month_balance']),
                '',
                '',
                '',
            )

            total_previous_month_balance += int(
                0 if row['previous_month_amount'] is None else row['previous_month_amount'])
            total_correction += 0
            total_receipts += int(0 if row['receipts'] is None else row['receipts'])
            total_carried_forward += int(
                0 if row['carried_forward'] is None else row['carried_forward'])
            total_earnings += int(0 if row['earnings'] is None else row['earnings'])
            total_consumption_tax += int(0 if row['consumption_tax'] is None else row['consumption_tax'])
            total_this_month_balance += int(0 if row['this_month_balance'] is None else row['this_month_balance'])
            new_data.append(data_line)

        # データ＜合計＞
        total_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
            branch.organization_code,  # 支店コード
            branch.name,  # 支店名
            target_date,  # 対象年月
            output_date,  # 出力日付
            '',  # 取引先コード
            '**  合　計　**',  # 取引先名称
            0 if total_previous_month_balance is None else "{:,}".format(total_previous_month_balance),
            0 if total_correction is None else "{:,}".format(total_correction),
            0 if total_receipts is None else "{:,}".format(total_receipts),
            0 if total_carried_forward is None else "{:,}".format(total_carried_forward),
            0 if total_earnings is None else "{:,}".format(total_earnings),
            0 if total_consumption_tax is None else "{:,}".format(total_consumption_tax),
            0 if total_this_month_balance is None else "{:,}".format(total_this_month_balance),
            '',
            '',
            '',
        )
        new_data.append(total_line)
        # データ＜総合計＞
        total_total_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
            branch.organization_code,  # 支店コード
            branch.name,  # 支店名
            target_date,  # 対象年月
            output_date,  # 出力日付
            '',  # 取引先コード
            '**  総合計　**',
            0 if total_previous_month_balance is None else "{:,}".format(total_previous_month_balance),
            0 if total_correction is None else "{:,}".format(total_correction),
            0 if total_receipts is None else "{:,}".format(total_receipts),
            0 if total_carried_forward is None else "{:,}".format(total_carried_forward),
            0 if total_earnings is None else "{:,}".format(total_earnings),
            0 if total_consumption_tax is None else "{:,}".format(total_consumption_tax),
            0 if total_this_month_balance is None else "{:,}".format(total_this_month_balance),
            '',
            '',
            '',
        )

        new_data.append(total_total_line)
        return "\n".join(new_data)

