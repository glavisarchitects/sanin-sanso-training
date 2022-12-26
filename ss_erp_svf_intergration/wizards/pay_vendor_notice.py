# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar
import base64


class PayVendorNotice(models.TransientModel):
    _name = 'pay.vendor.notice'

    partner_type = fields.Selection([('all', '全て'), ('manual_select', '選択'), ],
                                    string='支払先', default='manual_select')
    vendor_ids = fields.Many2many('res.partner', string='支払先')
    date_start = fields.Date(string='期日（開始）')
    date_end = fields.Date(string='期日（終了）')

    def _get_data_svf_r012(self):
        start_period = datetime.combine(self.date_start, datetime.min.time())
        end_period = datetime.combine(self.date_end, datetime.max.time())
        # 1 month previous period
        b1m_start_period = datetime.combine(self.date_start.replace(day=1) + relativedelta(months=-1),
                                            datetime.min.time())
        b1m_end_period = datetime.combine(
            b1m_start_period.replace(day=calendar.monthrange(b1m_start_period.year, b1m_start_period.month)[1]),
            datetime.max.time())
        # 2 month previous period
        b2m_start_period = datetime.combine(b1m_start_period + relativedelta(months=-1), datetime.min.time())
        b2m_end_period = datetime.combine(
            b2m_start_period.replace(day=calendar.monthrange(b2m_start_period.year, b2m_start_period.month)[1]),
            datetime.min.time())
        # 3 month previous period
        b3m_start_period = datetime.combine(b2m_start_period + relativedelta(months=-1), datetime.min.time())
        b3m_end_period = datetime.combine(
            b3m_start_period.replace(day=calendar.monthrange(b3m_start_period.year, b3m_start_period.month)[1]),
            datetime.min.time())
        # 4 month previous period
        b4m_start_period = datetime.combine(b3m_start_period + relativedelta(months=-1), datetime.min.time())
        b4m_end_period = datetime.combine(
            b4m_start_period.replace(day=calendar.monthrange(b4m_start_period.year, b4m_start_period.month)[1]),
            datetime.min.time())

        if self.partner_type == 'all' or not self.vendor_ids:
            domain_vendor = [('supplier_rank', '>', 0)]
        else:
            domain_vendor = [('id', 'in', self.vendor_ids.ids)]
        vendor_ids = self.env['res.partner'].search(domain_vendor).ids
        vendor_ids_str = f"({','.join(map(str, vendor_ids))})"
        query = f'''WITH
            x_payment_type AS (
            SELECT * FROM (VALUES('bank', '振込'),
                    ('transfer', '振替'),
                    ('bills', '手形'),
                    ('cash', '現金'),
                    ('paycheck', '小切手'),
                    ('branch_receipt', '他店入金'),
                    ('offset', '相殺')) AS t (x_type,x_value)
            ),
            acc_type AS (
            SELECT * FROM (VALUES('bank', '普通'),
                    ('chekcing', '当座')) AS t (x_type,x_value)
            ),
            acceptance_breakdown AS (
            SELECT
            *
            ,SUM(COALESCE(ab_amount.acceptance_breakdown_amount, 0)) OVER (PARTITION BY ab_amount.partner_id) as total_amount_breakdown
            --
            FROM(
            (
                SELECT
                        am.x_business_organization_id
                        ,am.partner_id
                        ,ABS(SUM(am.amount_total_signed)) acceptance_breakdown_amount
                FROM
                    account_move am
                LEFT JOIN res_partner rp ON rp.id = am.partner_id
                LEFT JOIN ss_erp_organization seo ON seo.id = am.x_business_organization_id

                WHERE
                am.payment_state = 'paid'
                AND am.move_type = 'in_invoice'
                AND am.partner_id in {vendor_ids_str}
                AND am.x_business_organization_id is not NULL
                AND am.invoice_date_due BETWEEN '{start_period}' and '{end_period}'
                GROUP BY
                am.x_business_organization_id
                ,am.partner_id))
                as ab_amount)

            ,in_refund AS (
            (SELECT
            *
            ,SUM(COALESCE(in_ref_amount.in_refund_ammount, 0)) OVER (PARTITION BY in_ref_amount.partner_id) as total_amount_in_refund
            FROM(
            (
                SELECT
                        am.x_business_organization_id
                        ,am.partner_id
                        ,ABS(SUM(am.amount_total_signed)) in_refund_ammount
                FROM
                    account_move am
                LEFT JOIN res_partner rp ON rp.id = am.partner_id
                LEFT JOIN ss_erp_organization seo ON seo.id = am.x_business_organization_id

                WHERE
                am.payment_state = 'paid'
                AND am.move_type = 'in_refund'
                AND am.partner_id in {vendor_ids_str}
                AND am.x_business_organization_id is not NULL
                AND am.invoice_date_due BETWEEN '{start_period}' and '{end_period}'
                GROUP BY
                am.x_business_organization_id
                ,am.partner_id)) as in_ref_amount))

            ,total_before_1_month AS (
            SELECT
            -- *
            unpaid_before_1_month.x_business_organization_id
            ,unpaid_before_1_month.partner_id
            ,unpaid_before_1_month.in_b1m_amount - unpaid_before_1_month.refund_b1m_amount unpaid
            FROM(
            (SELECT
            -- *
            total_b1m.x_business_organization_id
            ,total_b1m.partner_id
            ,SUM(COALESCE(total_b1m.acceptance_breakdown_amount, 0)) OVER (PARTITION BY total_b1m.partner_id) as in_b1m_amount
            ,SUM(COALESCE(total_b1m.in_refund_ammount, 0)) OVER (PARTITION BY total_b1m.partner_id) as refund_b1m_amount
            FROM(
            (
                SELECT
                        am.x_business_organization_id
                        ,am.partner_id
                        ,ABS(SUM(am.amount_total_signed)) acceptance_breakdown_amount
                FROM
                    account_move am
                LEFT JOIN res_partner rp ON rp.id = am.partner_id
                LEFT JOIN ss_erp_organization seo ON seo.id = am.x_business_organization_id

                WHERE
                am.payment_state = 'paid'
                AND am.move_type = 'in_invoice'
                AND am.partner_id in {vendor_ids_str}
                AND am.x_business_organization_id is not NUll
                AND am.partner_id is not NUll
                AND am.invoice_date_due BETWEEN '{b1m_start_period}' and '{b1m_end_period}'
                GROUP BY
                am.x_business_organization_id
                ,am.partner_id) as in_b1m
                LEFT JOIN
            (
                SELECT
                        am.x_business_organization_id refund_organization
                        ,am.partner_id refund_partner
                        ,ABS(SUM(am.amount_total_signed)) in_refund_ammount
                FROM
                    account_move am
                LEFT JOIN res_partner rp ON rp.id = am.partner_id
                LEFT JOIN ss_erp_organization seo ON seo.id = am.x_business_organization_id

                WHERE
                am.payment_state = 'paid'
                AND am.move_type = 'in_refund'
                AND am.invoice_date_due BETWEEN '{b1m_start_period}' and '{b1m_end_period}'
                GROUP BY
                am.x_business_organization_id
                ,am.partner_id) as refund_b1m ON refund_b1m.refund_organization = in_b1m.x_business_organization_id AND refund_b1m.refund_partner = in_b1m.partner_id AND refund_b1m.refund_partner is NOT NUll AND refund_b1m.refund_organization is not NULL

                ) as total_b1m))

            as unpaid_before_1_month)

            ,total_before_2_month AS (
            SELECT
            -- *
            unpaid_before_2_month.x_business_organization_id
            ,unpaid_before_2_month.partner_id
            ,unpaid_before_2_month.in_b2m_amount - unpaid_before_2_month.refund_b2m_amount unpaid
            FROM(
            (SELECT
            -- *
            total_b2m.x_business_organization_id
            ,total_b2m.partner_id
            ,SUM(COALESCE(total_b2m.acceptance_breakdown_amount, 0)) OVER (PARTITION BY total_b2m.partner_id) as in_b2m_amount
            ,SUM(COALESCE(total_b2m.in_refund_ammount, 0)) OVER (PARTITION BY total_b2m.partner_id) as refund_b2m_amount
            FROM(
            (
                SELECT
                        am.x_business_organization_id
                        ,am.partner_id
                        ,ABS(SUM(am.amount_total_signed)) acceptance_breakdown_amount
                FROM
                    account_move am
                LEFT JOIN res_partner rp ON rp.id = am.partner_id
                LEFT JOIN ss_erp_organization seo ON seo.id = am.x_business_organization_id

                WHERE
                am.payment_state = 'paid'
                AND am.move_type = 'in_invoice'
                AND am.partner_id in {vendor_ids_str}
                AND am.x_business_organization_id is not NUll
                AND am.partner_id is not NUll
                AND am.invoice_date_due BETWEEN '{b2m_start_period}' and '{b2m_end_period}'
                GROUP BY
                am.x_business_organization_id
                ,am.partner_id) as in_b2m
                LEFT JOIN
            (
                SELECT
                        am.x_business_organization_id refund_organization
                        ,am.partner_id refund_partner
                        ,ABS(SUM(am.amount_total_signed)) in_refund_ammount
                FROM
                    account_move am
                LEFT JOIN res_partner rp ON rp.id = am.partner_id
                LEFT JOIN ss_erp_organization seo ON seo.id = am.x_business_organization_id

                WHERE
                am.payment_state = 'paid'
                AND am.move_type = 'in_refund'
                AND am.partner_id in {vendor_ids_str}
                AND am.invoice_date_due BETWEEN '{b2m_start_period}' and '{b2m_end_period}'
                GROUP BY
                am.x_business_organization_id
                ,am.partner_id) as refund_b2m ON refund_b2m.refund_organization = in_b2m.x_business_organization_id AND refund_b2m.refund_partner = in_b2m.partner_id AND refund_b2m.refund_partner is NOT NUll AND refund_b2m.refund_organization is not NULL

                ) as total_b2m))

            as unpaid_before_2_month)

            ,total_before_3_month AS (
            SELECT
            -- *
            unpaid_before_3_month.x_business_organization_id
            ,unpaid_before_3_month.partner_id
            ,unpaid_before_3_month.in_b3m_amount - unpaid_before_3_month.refund_b3m_amount unpaid
            FROM(
            (SELECT
            -- *
            total_b3m.x_business_organization_id
            ,total_b3m.partner_id
            ,SUM(COALESCE(total_b3m.acceptance_breakdown_amount, 0)) OVER (PARTITION BY total_b3m.partner_id) as in_b3m_amount
            ,SUM(COALESCE(total_b3m.in_refund_ammount, 0)) OVER (PARTITION BY total_b3m.partner_id) as refund_b3m_amount
            FROM(
            (
                SELECT
                        am.x_business_organization_id
                        ,am.partner_id
                        ,ABS(SUM(am.amount_total_signed)) acceptance_breakdown_amount
                FROM
                    account_move am
                LEFT JOIN res_partner rp ON rp.id = am.partner_id
                LEFT JOIN ss_erp_organization seo ON seo.id = am.x_business_organization_id

                WHERE
                am.payment_state = 'paid'
                AND am.move_type = 'in_invoice'
                AND am.partner_id in {vendor_ids_str}
                AND am.x_business_organization_id is not NUll
                AND am.partner_id is not NUll
                AND am.invoice_date_due BETWEEN '{b3m_start_period}' and '{b3m_end_period}'
                GROUP BY
                am.x_business_organization_id
                ,am.partner_id) as in_b3m
                LEFT JOIN
            (
                SELECT
                        am.x_business_organization_id refund_organization
                        ,am.partner_id refund_partner
                        ,ABS(SUM(am.amount_total_signed)) in_refund_ammount
                FROM
                    account_move am
                LEFT JOIN res_partner rp ON rp.id = am.partner_id
                LEFT JOIN ss_erp_organization seo ON seo.id = am.x_business_organization_id

                WHERE
                am.payment_state = 'paid'
                AND am.move_type = 'in_refund'
                AND am.partner_id in {vendor_ids_str}
                AND am.invoice_date_due BETWEEN '{b3m_start_period}' and '{b3m_end_period}'
                GROUP BY
                am.x_business_organization_id
                ,am.partner_id) as refund_b3m ON refund_b3m.refund_organization = in_b3m.x_business_organization_id AND refund_b3m.refund_partner = in_b3m.partner_id AND refund_b3m.refund_partner is NOT NUll AND refund_b3m.refund_organization is not NULL

                ) as total_b3m))

            as unpaid_before_3_month)

            ,total_before_4_month AS (
            SELECT
            -- *
            unpaid_before_4_month.x_business_organization_id
            ,unpaid_before_4_month.partner_id
            ,unpaid_before_4_month.in_b4m_amount - unpaid_before_4_month.refund_b4m_amount unpaid
            FROM(
            (SELECT
            -- *
            total_b4m.x_business_organization_id
            ,total_b4m.partner_id
            ,SUM(COALESCE(total_b4m.acceptance_breakdown_amount, 0)) OVER (PARTITION BY total_b4m.partner_id) as in_b4m_amount
            ,SUM(COALESCE(total_b4m.in_refund_ammount, 0)) OVER (PARTITION BY total_b4m.partner_id) as refund_b4m_amount
            FROM(
            (
                SELECT
                        am.x_business_organization_id
                        ,am.partner_id
                        ,ABS(SUM(am.amount_total_signed)) acceptance_breakdown_amount
                FROM
                    account_move am
                LEFT JOIN res_partner rp ON rp.id = am.partner_id
                LEFT JOIN ss_erp_organization seo ON seo.id = am.x_business_organization_id

                WHERE
                am.payment_state = 'paid'
                AND am.move_type = 'in_invoice'
                AND am.partner_id in {vendor_ids_str}
                AND am.x_business_organization_id is not NUll
                AND am.partner_id is not NUll
                AND am.invoice_date_due BETWEEN '{b4m_start_period}' and '{b4m_end_period}'
                GROUP BY
                am.x_business_organization_id
                ,am.partner_id) as in_b4m
                LEFT JOIN
            (
                SELECT
                        am.x_business_organization_id refund_organization
                        ,am.partner_id refund_partner
                        ,ABS(SUM(am.amount_total_signed)) in_refund_ammount
                FROM
                    account_move am
                LEFT JOIN res_partner rp ON rp.id = am.partner_id
                LEFT JOIN ss_erp_organization seo ON seo.id = am.x_business_organization_id

                WHERE
                am.payment_state = 'paid'
                AND am.move_type = 'in_refund'
                AND am.partner_id in {vendor_ids_str}
                AND am.invoice_date_due BETWEEN '{b4m_start_period}' and '{b4m_end_period}'
                GROUP BY
                am.x_business_organization_id
                ,am.partner_id) as refund_b4m ON refund_b4m.refund_organization = in_b4m.x_business_organization_id AND refund_b4m.refund_partner = in_b4m.partner_id AND refund_b4m.refund_partner is NOT NUll AND refund_b4m.refund_organization is not NULL

                ) as total_b4m))

            as unpaid_before_4_month)


            SELECT
                DISTINCT ON (am.x_business_organization_id)
                '' print_date
                ,COALESCE(rp.zip, '') as recipient_zipcode
                ,CONCAT(pcs.name,rp.city,rp.street,rp.street2) as recipient_address
                ,COALESCE(rc.name, '') as recipient_company_name
                ,COALESCE(borg.name, '') as recipient_branch_name
                ,COALESCE(purp.name || '様', '') as recipient_manager_name
                ,COALESCE(org.name, '') as branch_name
            -- 	,COALESCE('〒' || org.organization_zip, '') as zip_code
                ,COALESCE(org.organization_zip, '') as zip_code
                ,CONCAT(orcs.name,org.organization_city,org.organization_street,org.organization_street2) as company_address
                ,COALESCE(org.organization_phone, '') as tel
                ,COALESCE(org.organization_fax, '') as fax
                ,'' as payment_date
            -- 	,SUM(COALESCE(ab.acceptance_breakdown_amount, 0)) OVER () - SUM(COALESCE(in_r.in_refund_ammount, 0)) OVER () as xx
            -- 	,SUM(COALESCE(ab.acceptance_breakdown_amount, 0)) OVER ()as xx
                ,to_char((ab.total_amount_breakdown - COALESCE(in_r.total_amount_in_refund, 0)), 'FM9,999,999,999,999,999,999') || ' 円'  as payment_amount -- 25 (1-5)
                ,borg.name  as acceptance_branch
                ,COALESCE(to_char((ab.acceptance_breakdown_amount), 'FM9,999,999,999,999,999,999'), '') as acceptance_price
                ,COALESCE(to_char((in_r.in_refund_ammount), 'FM9,999,999,999,999,999,999'), '') as acceptance_offset
                ,COALESCE(to_char((ab.total_amount_breakdown), 'FM9,999,999,999,999,999,999,999,999,999,999'), '') as acceptance_subtotal_price
                ,COALESCE(to_char((in_r.total_amount_in_refund), 'FM9,999,999,999,999,999,999'), '') as acceptance_subtotal_offset
                ,COALESCE(to_char((ab.total_amount_breakdown - in_r.total_amount_in_refund), 'FM9,999,999,999,999,999,999'), '')  as acceptance_total_amount -- = 25 (1-5)
                ,to_char(am.invoice_date_due, 'YYYY年MM月DD日')  as payment_due_date
                ,xpt.x_value AS payment_term
                ,COALESCE(to_char((ab.total_amount_breakdown - in_r.total_amount_in_refund), 'FM9,999,999,999,999,999,999'), '')  as payment_price -- = 25 (1-5)
                ,COALESCE(to_char((ab.total_amount_breakdown - in_r.total_amount_in_refund), 'FM9,999,999,999,999,999,999'), '')  as payment_total_amount -- = 25 (1-5)
                ,''  as unpaied_month_b1m
                ,''  as unpaied_due_date_b1m
                ,COALESCE(to_char(tb1m.unpaid, 'FM9,999,999,999,999,999,999'), '') as unpaied_price_b1m
                ,''  as unpaied_month_b2m
                ,''  as unpaied_due_date_b2m
                ,COALESCE(to_char(tb2m.unpaid, 'FM9,999,999,999,999,999,999'), '') as unpaied_price_b2m
                ,''  as unpaied_month_b3m
                ,''  as unpaied_due_date_b3m
                ,COALESCE(to_char(tb3m.unpaid, 'FM9,999,999,999,999,999,999'), '') as unpaied_price_b3m
                ,''  as unpaied_month_b4m
                ,''  as unpaied_due_date_b4m
                ,COALESCE(to_char(tb4m.unpaid, 'FM9,999,999,999,999,999,999'), '') as unpaied_price_b4m
                ,COALESCE(to_char(tb1m.unpaid + tb4m.unpaid + tb4m.unpaid + tb4m.unpaid, 'FM9,999,999,999,999,999,999'), '') as unpaied_total_price
                ,COALESCE(rp.ref, '') as reference_code
                ,COALESCE(rp.x_fax, '') as destination_fax
                ,COALESCE(rb.name, '') as payee_bank_name
                ,COALESCE(rpb.x_bank_branch, '') as payee_bank_branch_name
                ,COALESCE(xat.x_value, '') as payee_bank_type
                ,COALESCE(rpb.acc_number, '') as payee_bank_number
                ,COALESCE(rpb.acc_holder_name, '') as payee_bank_holder_name
                ,COALESCE(am.narration, '') as info_text


            FROM
                account_move am
                LEFT JOIN res_partner rp ON rp.id = am.partner_id
                LEFT JOIN res_company rc ON rc.id = am.company_id
                LEFT JOIN res_country_state pcs ON pcs.id = rp.state_id
                LEFT JOIN res_users pu ON pu.id = rp.x_purchase_user_id
                LEFT JOIN res_partner purp ON purp.id = pu.partner_id
                LEFT JOIN ss_erp_organization borg ON borg.id = am.x_business_organization_id
                LEFT JOIN ss_erp_organization org ON org.id = am.x_organization_id
                LEFT JOIN res_country_state orcs ON orcs.id = org.organization_state_id
                INNER JOIN acceptance_breakdown ab ON ab.x_business_organization_id = am.x_business_organization_id AND ab.partner_id = am.partner_id
                LEFT JOIN in_refund in_r ON in_r.x_business_organization_id = am.x_business_organization_id AND in_r.partner_id = am.partner_id
                LEFT JOIN x_payment_type xpt ON rp.x_payment_type = xpt.x_type
                LEFT JOIN total_before_1_month tb1m ON tb1m.x_business_organization_id = am.x_business_organization_id AND tb1m.partner_id = am.partner_id
                LEFT JOIN total_before_2_month tb2m ON tb2m.x_business_organization_id = am.x_business_organization_id AND tb2m.partner_id = am.partner_id
                LEFT JOIN total_before_3_month tb3m ON tb3m.x_business_organization_id = am.x_business_organization_id AND tb3m.partner_id = am.partner_id
                LEFT JOIN total_before_4_month tb4m ON tb4m.x_business_organization_id = am.x_business_organization_id AND tb4m.partner_id = am.partner_id
                LEFT JOIN res_partner_bank rpb ON rpb.partner_id = rp.id
                LEFT JOIN res_bank rb ON rb.id = rpb.bank_id
                LEFT JOIN acc_type xat ON rpb.acc_type = xat.x_type
            -- 	LEFT JOIN res_partner_bank orpb ON orpb.organization_id = org.id
            -- 	LEFT JOIN res_bank orb ON orb.id = orpb.
            
            WHERE
            am.payment_state = 'paid'
            AND am.partner_id in {vendor_ids_str}
            AND am.x_business_organization_id is not NULL
            AND am.invoice_date_due BETWEEN '{start_period}' and '{end_period}'

            -- 	GROUP BY
            -- 	am.x_organization_id
            -- 	,am.partner_id

            ORDER BY am.x_business_organization_id, rp.id

'''

        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def pay_vendor_notice_svf_export(self):
        data_file = [
            '"print_date","recipient_zipcode","recipient_address","recipient_company_name","recipient_branch_name","recipient_manager_name","branch_name","zip_code","company_address","tel","fax","payment_date","payment_amount","acceptance_branch","acceptance_price","acceptance_offset","acceptance_subtotal_price","acceptance_subtotal_offset","acceptance_total_amount","payment_due_date","payment_term","payment_price","payment_total_amount","unpaied_month","unpaied_due_date","unpaied_price","unpaied_total_price","reference_code","destination_fax","payee_bank_name","payee_bank_branch_name","payee_bank_type","payee_bank_number","payee_bank_holder_name","info_text"']
        data_query = self._get_data_svf_r012()

        if not data_query:
            raise UserError(_("出力対象のデータがありませんでした。"))
        for line in data_query:
            one_line_data = ""
            for key, values in line.items():
                one_line_data += '"' + values + '",'
            data_file.append(one_line_data)
        data_send = "\n".join(data_file)
        data_send = data_send[0:-1]

        # b = data_send.encode('Shift-JIS')
        # vals = {
        #     'name': '支払通知書' '.csv',
        #     'datas': base64.b64encode(b).decode('Shift-JIS'),
        #     'type': 'binary',
        #     'res_model': 'ir.ui.view',
        #     'x_no_need_save': True,
        #     'res_id': False,
        # }
        #
        # file_txt = self.env['ir.attachment'].create(vals)
        #
        # return {
        #     'type': 'ir.actions.act_url',
        #     'url': '/web/content/' + str(file_txt.id) + '?download=true',
        #     'target': 'new',
        # }

        return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_send, type_report='R012')
