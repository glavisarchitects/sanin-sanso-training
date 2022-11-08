# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
import requests
import base64
import json


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_data_svf_r002(self):
        registration_number = self.env['ir.config_parameter'].sudo().get_param('invoice_report.registration_number') if \
            self.env['ir.config_parameter'].sudo().get_param('invoice_report.registration_number') else ''

        now = datetime.now()

        first_day_current_month = datetime.combine(now.replace(day=1), datetime.min.time())
        last_day_current_month = datetime.combine(now.replace(day=calendar.monthrange(now.year, now.month)[1]),
                                                  datetime.max.time())

        current_date_last_month = now + relativedelta(months=-1)
        first_day_last_month = datetime.combine(current_date_last_month.replace(day=1), datetime.min.time())
        last_day_last_month = datetime.combine(current_date_last_month.replace(
            day=calendar.monthrange(current_date_last_month.year, current_date_last_month.month)[1]),
            datetime.max.time())

        str_due_date_start = first_day_last_month.strftime("%Y年%m月%d日")
        str_due_date_end = last_day_last_month.strftime("%Y年%m月%d日")

        r002_tax10_id = self.env['ir.config_parameter'].sudo().get_param('R002_tax10_id')
        r002_tax8_id = self.env['ir.config_parameter'].sudo().get_param('R002_tax8_id')
        r002_reduction_tax8_id = self.env['ir.config_parameter'].sudo().get_param('R002_reduction_tax8_id')
        r002_tax_exempt_id = self.env['ir.config_parameter'].sudo().get_param('R002_tax_exempt_id')

        if not r002_tax10_id or not r002_tax8_id or not r002_reduction_tax8_id or not r002_tax_exempt_id:
            raise UserError('パラメータで税勘定を設定してください')

        #
        query = f'''
        
        WITH x_payment_type AS (
        SELECT * FROM (VALUES('bank', '振込'),
            ('transfer', '振替'),
            ('bills', '手形'),
            ('cash', '現金'),
            ('paycheck', '小切手'),
            ('branch_receipt', '他店入金'),
            ('offset', '相殺')) AS t (x_type,x_value)
        )	,
        deposit_amount AS (
        select ap.partner_id, ap.x_organization_id, sum(ap.amount) deposit_amount from account_payment ap
            left join account_move am on am.id = ap.move_id
            left join account_journal aj on am.journal_id = aj.id
            where am.date BETWEEN '{first_day_current_month}' 
            and '{last_day_current_month}' and ap.payment_type = 'inbound'
            and ap.partner_id = '{self.partner_id.id}' and ap.x_organization_id = '{self.x_organization_id.id}'
            and aj.x_is_construction = False
            GROUP BY ap.partner_id, ap.x_organization_id),
            
        -- PREVIOUS MONTH AMOUNT
        previous_month_invoice AS (
        SELECT
            tb1.partner_id,
            tb1.x_organization_id,
            ABS(SUM ( tb1.amount )) AS previous_month_amount
        FROM
        (
        SELECT
            am.partner_id,
            am.x_organization_id,
            CASE WHEN am.move_type = 'out_invoice' THEN am.amount_total ELSE -am.amount_total END AS amount 
        FROM
        account_move am
        left join account_journal aj on am.journal_id = aj.id
        WHERE
        am.STATE = 'posted' 
        AND am.move_type IN ( 'out_invoice', 'out_refund' )
        AND am.x_organization_id = {self.x_organization_id.id}
        AND am.partner_id = {self.partner_id.id}
        AND aj.x_is_construction = False
        AND am.date BETWEEN '{first_day_last_month}' and '{last_day_last_month}'
        ) tb1 
        GROUP BY
                tb1.partner_id,
                tb1.x_organization_id 
        ),         
         
        -- PREVIOUS MONTH BALANCE   
        previous_month_balance AS (
            SELECT
                tb3.partner_id,
                tb3.x_organization_id,
                ABS(SUM ( tb3.amount )) AS previous_month_balance
            FROM
            (
                    SELECT
                        am.partner_id,
                        am.x_organization_id,
                        CASE WHEN am.move_type = 'out_invoice' THEN am.amount_total ELSE -am.amount_total END AS amount 
                    FROM
                    account_move am
                    left join account_journal aj on am.journal_id = aj.id
                    WHERE
                    am.STATE = 'posted' 
                    AND am.move_type IN ( 'out_invoice', 'out_refund' )
                    AND am.date BETWEEN '{first_day_last_month}' and '{last_day_last_month}' 		
                    AND am.x_organization_id = {self.x_organization_id.id}
                    AND am.partner_id = {self.partner_id.id}
                    AND aj.x_is_construction = False
                    UNION ALL
                        SELECT
                        ap.partner_id,
                        ap.x_organization_id,
                        CASE WHEN ap.payment_type = 'inbound' THEN- ap.amount ELSE ap.amount END 
                    FROM
                    account_payment ap
                    LEFT JOIN account_move am ON ap.move_id = am.ID 
                    left join account_journal aj on am.journal_id = aj.id
                    WHERE
                    ap.payment_type IN ( 'inbound', 'outbound' ) 
                    AND ap.move_id IS NOT NULL
                    AND am.date BETWEEN '{first_day_last_month}' and '{last_day_last_month}' 		
                    AND am.x_organization_id = {self.x_organization_id.id}
                    AND aj.x_is_construction = False
                    AND ap.partner_id = {self.partner_id.id}
                    ) tb3 
                    GROUP BY
                            tb3.partner_id,
                            tb3.x_organization_id 
            ), 
        -- PREVIOUS DEPOSIT LIST         
        
        previous_month_money_collect_list AS (
            SELECT						
            to_char(am.date,'MM/DD') AS date,
            am.name AS slip_number,
            NULL AS detail_number,
            NULL AS product_id,
            xpt.x_value AS product_name,
            NULL AS quantity,
            NULL AS unit,
            0 AS unit_price,
            CASE WHEN ap.payment_type = 'inbound' THEN ap.amount ELSE -ap.amount END AS price,
            NULL AS tax_rate,
            NULL AS summary
            FROM
            account_payment ap
            LEFT JOIN account_move am ON ap.move_id = am.ID
            LEFT JOIN x_payment_type xpt ON ap.x_receipt_type = xpt.x_type
            LEFT JOIN account_journal aj on am.journal_id = aj.id
            WHERE
                    ap.payment_type IN ( 'inbound', 'outbound' ) 
                    AND ap.move_id IS NOT NULL 
                    AND ap.partner_id IS NOT NULL
                    AND ap.partner_id = {self.partner_id.id}
                    AND am.date BETWEEN '{first_day_last_month}' and '{last_day_last_month}' 		
                    AND am.x_organization_id = {self.x_organization_id.id}
                    AND aj.x_is_construction = False
            ),

        previous_month_money_collect_sum AS (
            SELECT
                NULL, 																	-- date
                NULL,																		-- slip_number
                NULL,																		-- detail_number
                NULL,																		-- product_id
                '*** 入　金　計 ***' AS product_name,			-- product_name
                NULL,																		-- quantity
                NULL,																		-- unit
                0,																		-- unit_price
                ABS(sum(tb4.amount)) AS price,					-- quantity
                NULL,																		-- price
                NULL      															-- tax_rate             	    
            FROM 
                (
                SELECT
                ap.partner_id,
                ap.x_organization_id,
                CASE WHEN ap.payment_type = 'inbound' THEN ap.amount ELSE -ap.amount END AS amount
                FROM
                        account_payment ap
                        LEFT JOIN account_move am ON ap.move_id = am.ID
                        LEFT JOIN account_journal aj on am.journal_id = aj.id
                WHERE
                        ap.payment_type IN ( 'inbound', 'outbound' ) 
                        AND ap.move_id IS NOT NULL 
                        AND ap.partner_id = {self.partner_id.id}
                        AND am.date BETWEEN '{first_day_last_month}' and '{last_day_last_month}' 	
                        AND am.x_organization_id = {self.x_organization_id.id}
                        AND aj.x_is_construction = False
                )tb4
                GROUP BY
                            tb4.partner_id,
                            tb4.x_organization_id 
            ),                         
        -- END        
            
        org_bank as (
        select 
            rpb.organization_id,
            concat('振込先口座　　',rb.name,rpb.x_bank_branch,'（',CASE When rpb.acc_type = 'bank' then '通常' ELSE '当座' END,'）',rpb.x_bank_branch_number) as payee_info	
        from res_partner_bank rpb
        left join res_bank rb on rpb.bank_id = rb.id
        where rpb.organization_id is not null
        ),
        -- SUM TAX REGION
        sum_tax_10 as (
        select am.id move_id,
        amlat.account_tax_id tax_id, 
        ROUND(sum(aml.price_subtotal/10)) tax_amount_rate10, 
        ROUND(sum(aml.price_subtotal)) price_total_tax_rate10 
        from account_move_line aml
        left join account_move am ON am.id = aml.move_id
        left join account_move_line_account_tax_rel amlat ON amlat.account_move_line_id = aml.id        
        where amlat.account_tax_id = {r002_tax10_id} and am.id = {self.id}
        GROUP BY am.id, amlat.account_tax_id
        ),
        sum_tax_8 as (
        select am.id move_id,
        amlat.account_tax_id tax_id, 
        ROUND(sum(aml.price_subtotal/8)) tax_amount_rate8, 
        ROUND(sum(aml.price_subtotal)) price_total_tax_rate8 
        from account_move_line aml
        left join account_move am ON am.id = aml.move_id
        left join account_move_line_account_tax_rel amlat ON amlat.account_move_line_id = aml.id
        where amlat.account_tax_id = {r002_tax8_id} and am.id = {self.id}
        GROUP BY am.id, amlat.account_tax_id
        ),
        sum_reduce_tax_8 as (
        select am.id move_id,
        amlat.account_tax_id tax_id, 
        ROUND(sum(aml.price_subtotal/8)) price_total_reduced_tax_rate8, 
        ROUND(sum(aml.price_subtotal)) tax_amount_reduced_tax_rate8 
        from account_move_line aml
        left join account_move am ON am.id = aml.move_id
        left join account_move_line_account_tax_rel amlat ON amlat.account_move_line_id = aml.id
        where amlat.account_tax_id = {r002_reduction_tax8_id} and am.id = {self.id}
        GROUP BY am.id, amlat.account_tax_id
        ),
        sum_no_tax as (
        select 
        am.id move_id,
        amlat.account_tax_id tax_id, 
        sum(aml.price_subtotal) price_total_no_tax, 
        0 tax_amount_no_tax 
        from account_move_line aml
        left join account_move am ON am.id = aml.move_id
        left join account_move_line_account_tax_rel amlat ON amlat.account_move_line_id = aml.id
        where amlat.account_tax_id = {r002_tax_exempt_id} and am.id = {self.id}
        GROUP BY am.id, amlat.account_tax_id
        ),
        sale_tax AS (
        SELECT atsol.sale_order_line_id as order_line_id, string_agg(atx.name,', ') AS tax_account FROM account_tax_sale_order_line_rel atsol
        LEFT JOIN account_tax atx ON atsol.account_tax_id = atx.id
        GROUP BY atsol.sale_order_line_id
        ),                
        -- PRODUCT TRANSACTION DETAIL
        product_transaction AS 
        (                
        SELECT
            to_char(sp.date, 'MM/DD') AS date,
            sp.name AS slip_number,
            NULL,
            sml.product_id::text,
            pt.name AS product_name,            
            sum(sml.qty_done)::text AS quantity,
            tb.value AS unit,
            sol.price_unit AS unit_price,
            sol.price_subtotal AS price,
            st.tax_account AS tax_rate,
            COALESCE(sol.x_remarks, '') summary
        FROM stock_move_line sml
        LEFT JOIN stock_move sm ON sml.move_id = sm.id
        LEFT JOIN stock_picking sp on sm.picking_id = sp.id
        LEFT JOIN sale_order so ON sp.sale_id = so.id
        LEFT JOIN sale_order_line sol ON sol.order_id = so.id AND sol.product_id = sml.product_id AND sml.product_uom_id = sol.product_uom
        LEFT JOIN sale_order_line_invoice_rel solr ON solr.order_line_id  = sol.id 
        LEFT JOIN account_move_line aml ON aml.id = solr.invoice_line_id
        LEFT JOIN account_move am ON aml.move_id = am.id
        LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
        LEFT JOIN product_product pp ON sml.product_id = pp.id
        LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
        LEFT JOIN sale_tax st ON sol.id = st.order_line_id
        LEFT JOIN (SELECT * FROM ir_translation where name = 'uom.uom,name' and state='translated')tb on tb.res_id = sml.product_uom_id
        WHERE sml.state = 'done' AND am.id = {self.id} AND spt.code = 'outgoing'
        GROUP BY
            sp.date,
            sp.name,
            sml.product_id,
            pt.name,
            tb.value,
            sol.price_unit,
            sol.price_subtotal,
            st.tax_account,
            sol.x_remarks
        ),
    
        -- PRODUCT SUM 
        invoice_product_group AS (
            SELECT
            NULL,            -- date
            NULL,            -- slip_number
            NULL,            -- detail_number
            pt1.product_id::text,									
            '***' || pt.name || '計***' AS product_name,
            NULL,            -- quantity
            NULL,            -- unit
            0,            -- unit_price
            SUM(price) AS price,
            NULL,            -- tax_rate
            NULL             -- summary
            FROM product_transaction pt1
                LEFT JOIN product_product pp ON pt1.product_id::int = pp.id
                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                GROUP BY pt1.product_id,pt.name
        ),
        transaction_detail AS 
        (SELECT {self.id} AS invoice_move_id,* FROM 
        previous_month_money_collect_list
        UNION ALL 
        SELECT {self.id},* FROM previous_month_money_collect_sum				
        UNION ALL
        SELECT {self.id},* FROM (
        SELECT * FROM product_transaction
        UNION ALL 
        SELECT * FROM invoice_product_group
        ORDER BY product_id, date asc) tb10)
        
        SELECT 
                am.name AS invoice_no
              , rp.zip as zip
                , concat(rcs.name,rp.city,rp.street,rp.street2) as address
                , concat(rp.name,'様') as customer_name
                , to_char(now(), 'YYYY年MM月DD日')  as output_date
                , '{registration_number}' as registration_number
                , seo.name
                , concat(he.job_title,':',he.name) as responsible_person
                , seo.organization_zip as organization_zip
                , concat(rcs2.name,seo.organization_city,seo.organization_street,seo.organization_street2) as organization_address
                , concat('TEL:', seo.organization_phone) as organization_phone
                , concat('FAX:', seo.organization_fax) as organization_fax
                , COALESCE(am.amount_total, 0) AS this_month_amount
                , to_char(am.invoice_date_due, 'YYYY年MM月DD日')  as invoice_date_due
                , COALESCE(pmi.previous_month_amount, 0) AS previous_month_amount
                , COALESCE(da.deposit_amount, 0) AS deposit_amount
                , COALESCE(pmb.previous_month_balance, 0) AS previous_month_balance
                , am.amount_untaxed AS this_month_purchase
                , am.amount_tax AS consumption_tax
                , concat('{str_due_date_start}','~','{str_due_date_end}','締切') as due_date
                , td.date
                , td.slip_number
                , td.detail_number
                , td.product_name
                , td.quantity
                , td.unit
                , td.unit_price
                , td.price
                , td.tax_rate
                , td.summary
                , st10.price_total_tax_rate10
                , st8.price_total_tax_rate8
                , srt8.price_total_reduced_tax_rate8
                , snt.price_total_no_tax
                , st10.tax_amount_rate10
                , st8.tax_amount_rate8
                , srt8.tax_amount_reduced_tax_rate8
                , snt.tax_amount_no_tax
                , am.amount_untaxed AS price_total
                , am.amount_tax AS price_total_tax
                , ob.payee_info
        FROM transaction_detail td
        LEFT JOIN account_move am ON td.invoice_move_id = am.id
        LEFT JOIN deposit_amount da ON am.x_organization_id = da.x_organization_id AND am.partner_id = da.partner_id
        LEFT JOIN res_partner rp ON am.partner_id = rp.id
        LEFT JOIN res_country_state rcs ON rp.state_id = rcs.id
        LEFT JOIN ss_erp_organization seo ON am.x_organization_id = seo.id
        LEFT JOIN hr_employee he ON seo.responsible_person = he.id
        LEFT JOIN res_country_state rcs2 ON seo.organization_state_id = rcs2.id
        LEFT JOIN previous_month_invoice pmi ON am.x_organization_id = pmi.x_organization_id AND am.partner_id = pmi.partner_id
        LEFT JOIN previous_month_balance pmb ON am.x_organization_id = pmb.x_organization_id AND am.partner_id = pmb.partner_id
        LEFT JOIN sum_tax_10 st10 ON st10.move_id = am.id
        LEFT JOIN sum_tax_8 st8 ON st8.move_id = am.id
        LEFT JOIN sum_reduce_tax_8 srt8 ON srt8.move_id = am.id
        LEFT JOIN sum_no_tax snt ON snt.move_id = am.id
        LEFT JOIN org_bank ob ON am.x_organization_id = ob.organization_id
        WHERE am.id = {self.id}				
        '''

        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def _get_data_svf_r002_construction(self):
        registration_number = self.env['ir.config_parameter'].sudo().get_param('invoice_report.registration_number') if \
            self.env['ir.config_parameter'].sudo().get_param('invoice_report.registration_number') else ''

        now = datetime.now()

        first_day_current_month = datetime.combine(now.replace(day=1), datetime.min.time())
        last_day_current_month = datetime.combine(now.replace(day=calendar.monthrange(now.year, now.month)[1]),
                                                  datetime.max.time())

        current_date_last_month = now + relativedelta(months=-1)
        first_day_last_month = datetime.combine(current_date_last_month.replace(day=1), datetime.min.time())
        last_day_last_month = datetime.combine(current_date_last_month.replace(
            day=calendar.monthrange(current_date_last_month.year, current_date_last_month.month)[1]),
            datetime.max.time())

        str_due_date_start = first_day_last_month.strftime("%Y年%m月%d日")
        str_due_date_end = last_day_last_month.strftime("%Y年%m月%d日")

        r002_tax10_id = self.env['ir.config_parameter'].sudo().get_param('R002_tax10_id')
        r002_tax8_id = self.env['ir.config_parameter'].sudo().get_param('R002_tax8_id')
        r002_reduction_tax8_id = self.env['ir.config_parameter'].sudo().get_param('R002_reduction_tax8_id')
        r002_tax_exempt_id = self.env['ir.config_parameter'].sudo().get_param('R002_tax_exempt_id')

        if not r002_tax10_id or not r002_tax8_id or not r002_reduction_tax8_id or not r002_tax_exempt_id:
            raise UserError('パラメータで税勘定を設定してください')

        #
        query = f'''

        WITH x_payment_type AS (
        SELECT * FROM (VALUES('bank', '振込'),
            ('transfer', '振替'),
            ('bills', '手形'),
            ('cash', '現金'),
            ('paycheck', '小切手'),
            ('branch_receipt', '他店入金'),
            ('offset', '相殺')) AS t (x_type,x_value)
        )	,
        deposit_amount AS (
        select ap.partner_id, ap.x_organization_id, sum(ap.amount) deposit_amount from account_payment ap
            left join account_move am on am.id = ap.move_id
            left join account_journal aj on am.journal_id = aj.id
            where am.date BETWEEN '{first_day_current_month}' 
            and '{last_day_current_month}' and ap.payment_type = 'inbound'
            and ap.partner_id = '{self.partner_id.id}' and ap.x_organization_id = '{self.x_organization_id.id}'
            and aj.x_is_construction = True
            GROUP BY ap.partner_id, ap.x_organization_id),

        -- PREVIOUS MONTH AMOUNT
        previous_month_invoice AS (
        SELECT
            tb1.partner_id,
            tb1.x_organization_id,
            ABS(SUM ( tb1.amount )) AS previous_month_amount
        FROM
        (
        SELECT
            am.partner_id,
            am.x_organization_id,
            CASE WHEN am.move_type = 'out_invoice' THEN am.amount_total ELSE -am.amount_total END AS amount 
        FROM
        account_move am
        left join account_journal aj on am.journal_id = aj.id
        WHERE
        am.STATE = 'posted' 
        AND am.move_type IN ( 'out_invoice', 'out_refund' )
        AND am.x_organization_id = {self.x_organization_id.id}
        AND am.partner_id = {self.partner_id.id}
        AND aj.x_is_construction = True
        AND am.date BETWEEN '{first_day_last_month}' and '{last_day_last_month}'
        ) tb1 
        GROUP BY
                tb1.partner_id,
                tb1.x_organization_id 
        ),         

        -- PREVIOUS MONTH BALANCE   
        previous_month_balance AS (
            SELECT
                tb3.partner_id,
                tb3.x_organization_id,
                ABS(SUM ( tb3.amount )) AS previous_month_balance
            FROM
            (
                    SELECT
                        am.partner_id,
                        am.x_organization_id,
                        CASE WHEN am.move_type = 'out_invoice' THEN am.amount_total ELSE -am.amount_total END AS amount 
                    FROM
                    account_move am
                    left join account_journal aj on am.journal_id = aj.id
                    WHERE
                    am.STATE = 'posted' 
                    AND am.move_type IN ( 'out_invoice', 'out_refund' )
                    AND am.date BETWEEN '{first_day_last_month}' and '{last_day_last_month}' 		
                    AND am.x_organization_id = {self.x_organization_id.id}
                    AND am.partner_id = {self.partner_id.id}
                    AND aj.x_is_construction = True
                    UNION ALL
                        SELECT
                        ap.partner_id,
                        ap.x_organization_id,
                        CASE WHEN ap.payment_type = 'inbound' THEN- ap.amount ELSE ap.amount END 
                    FROM
                    account_payment ap
                    LEFT JOIN account_move am ON ap.move_id = am.ID 
                    left join account_journal aj on am.journal_id = aj.id
                    WHERE
                    ap.payment_type IN ( 'inbound', 'outbound' ) 
                    AND ap.move_id IS NOT NULL
                    AND am.date BETWEEN '{first_day_last_month}' and '{last_day_last_month}' 		
                    AND am.x_organization_id = {self.x_organization_id.id}
                    AND aj.x_is_construction = True
                    AND ap.partner_id = {self.partner_id.id}
                    ) tb3 
                    GROUP BY
                            tb3.partner_id,
                            tb3.x_organization_id 
            ), 
        -- PREVIOUS DEPOSIT LIST         

        previous_month_money_collect_list AS (
            SELECT						
            to_char(am.date,'MM/DD') AS date,
            am.name AS slip_number,
            NULL AS detail_number,
            NULL AS product_id,
            xpt.x_value AS product_name,
            NULL AS quantity,
            NULL AS unit,
            0 AS unit_price,
            CASE WHEN ap.payment_type = 'inbound' THEN ap.amount ELSE -ap.amount END AS price,
            NULL AS tax_rate,
            NULL AS summary
            FROM
            account_payment ap
            LEFT JOIN account_move am ON ap.move_id = am.ID
            LEFT JOIN x_payment_type xpt ON ap.x_receipt_type = xpt.x_type
            LEFT JOIN account_journal aj on am.journal_id = aj.id
            WHERE
                    ap.payment_type IN ( 'inbound', 'outbound' ) 
                    AND ap.move_id IS NOT NULL 
                    AND ap.partner_id IS NOT NULL
                    AND ap.partner_id = {self.partner_id.id}
                    AND am.date BETWEEN '{first_day_last_month}' and '{last_day_last_month}' 		
                    AND am.x_organization_id = {self.x_organization_id.id}
                    AND aj.x_is_construction = True
            ),

        previous_month_money_collect_sum AS (
            SELECT
                NULL, 																	-- date
                NULL,																		-- slip_number
                NULL,																		-- detail_number
                NULL,																		-- product_id
                '*** 入　金　計 ***' AS product_name,			-- product_name
                NULL,																		-- quantity
                NULL,																		-- unit
                0,																		-- unit_price
                ABS(sum(tb4.amount)) AS price,					-- quantity
                NULL,																		-- price
                NULL      															-- tax_rate             	    
            FROM 
                (
                SELECT
                ap.partner_id,
                ap.x_organization_id,
                CASE WHEN ap.payment_type = 'inbound' THEN ap.amount ELSE -ap.amount END AS amount
                FROM
                        account_payment ap
                        LEFT JOIN account_move am ON ap.move_id = am.ID
                        LEFT JOIN account_journal aj on am.journal_id = aj.id
                WHERE
                        ap.payment_type IN ( 'inbound', 'outbound' ) 
                        AND ap.move_id IS NOT NULL 
                        AND ap.partner_id = {self.partner_id.id}
                        AND am.date BETWEEN '{first_day_last_month}' and '{last_day_last_month}' 	
                        AND am.x_organization_id = {self.x_organization_id.id}
                        AND aj.x_is_construction = True
                )tb4
                GROUP BY
                            tb4.partner_id,
                            tb4.x_organization_id 
            ),                         
        -- END        

        org_bank as (
        select 
            rpb.organization_id,
            concat('振込先口座　　',rb.name,rpb.x_bank_branch,'（',CASE When rpb.acc_type = 'bank' then '通常' ELSE '当座' END,'）',rpb.x_bank_branch_number) as payee_info	
        from res_partner_bank rpb
        left join res_bank rb on rpb.bank_id = rb.id
        where rpb.organization_id is not null
        ),
        -- SUM TAX REGION
        sum_tax_10 as (
        select am.id move_id,
        amlat.account_tax_id tax_id, 
        ROUND(sum(aml.price_subtotal/10)) tax_amount_rate10, 
        ROUND(sum(aml.price_subtotal)) price_total_tax_rate10 
        from account_move_line aml
        left join account_move am ON am.id = aml.move_id
        left join account_move_line_account_tax_rel amlat ON amlat.account_move_line_id = aml.id        
        where amlat.account_tax_id = {r002_tax10_id} and am.id = {self.id}
        GROUP BY am.id, amlat.account_tax_id
        ),
        sum_tax_8 as (
        select am.id move_id,
        amlat.account_tax_id tax_id, 
        ROUND(sum(aml.price_subtotal/8)) tax_amount_rate8, 
        ROUND(sum(aml.price_subtotal)) price_total_tax_rate8 
        from account_move_line aml
        left join account_move am ON am.id = aml.move_id
        left join account_move_line_account_tax_rel amlat ON amlat.account_move_line_id = aml.id
        where amlat.account_tax_id = {r002_tax8_id} and am.id = {self.id}
        GROUP BY am.id, amlat.account_tax_id
        ),
        sum_reduce_tax_8 as (
        select am.id move_id,
        amlat.account_tax_id tax_id, 
        ROUND(sum(aml.price_subtotal/8)) price_total_reduced_tax_rate8, 
        ROUND(sum(aml.price_subtotal)) tax_amount_reduced_tax_rate8 
        from account_move_line aml
        left join account_move am ON am.id = aml.move_id
        left join account_move_line_account_tax_rel amlat ON amlat.account_move_line_id = aml.id
        where amlat.account_tax_id = {r002_reduction_tax8_id} and am.id = {self.id}
        GROUP BY am.id, amlat.account_tax_id
        ),
        sum_no_tax as (
        select 
        am.id move_id,
        amlat.account_tax_id tax_id, 
        sum(aml.price_subtotal) price_total_no_tax, 
        0 tax_amount_no_tax 
        from account_move_line aml
        left join account_move am ON am.id = aml.move_id
        left join account_move_line_account_tax_rel amlat ON amlat.account_move_line_id = aml.id
        where amlat.account_tax_id = {r002_tax_exempt_id} and am.id = {self.id}
        GROUP BY am.id, amlat.account_tax_id
        ),
        invoice_tax AS (
        SELECT aal.account_move_line_id as move_line_id, string_agg(atx.name,', ') AS tax_account FROM account_move_line_account_tax_rel aal
        LEFT JOIN account_tax atx ON aal.account_tax_id = atx.id
        GROUP BY aal.account_move_line_id
        ),                
        -- PRODUCT TRANSACTION DETAIL
        product_transaction AS 
        (                
        SELECT
            to_char(am.invoice_date, 'MM/DD') AS date,
            am.name AS slip_number,
            NULL,
            aml.product_id::text,
            pt.name AS product_name,            
            aml.quantity::text AS quantity,
            tb.value AS unit,
            aml.price_unit AS unit_price,
            aml.price_subtotal AS price,
            it.tax_account AS tax_rate,
            '' AS summary
        FROM account_move_line aml
        LEFT JOIN account_move am ON aml.move_id = am.id
        LEFT JOIN product_product pp ON aml.product_id = pp.id
        LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
        LEFT JOIN invoice_tax it ON aml.id = it.move_line_id
        LEFT JOIN (SELECT * FROM ir_translation where name = 'uom.uom,name' and state='translated')tb on tb.res_id = aml.product_uom_id
        WHERE am.id = {self.id} and aml.product_id is not null
        ),

        transaction_detail AS 
        (SELECT {self.id} AS invoice_move_id,* FROM 
        previous_month_money_collect_list
        UNION ALL 
        SELECT {self.id},* FROM previous_month_money_collect_sum				
        UNION ALL
        SELECT {self.id},* FROM (
        SELECT * FROM product_transaction
        ORDER BY product_id, date asc) tb10)

        SELECT 
                am.name AS invoice_no
              , rp.zip as zip
                , concat(rcs.name,rp.city,rp.street,rp.street2) as address
                , concat(rp.name,'様') as customer_name
                , to_char(now(), 'YYYY年MM月DD日')  as output_date
                , '{registration_number}' as registration_number
                , seo.name
                , concat(he.job_title,':',he.name) as responsible_person
                , seo.organization_zip as organization_zip
                , concat(rcs2.name,seo.organization_city,seo.organization_street,seo.organization_street2) as organization_address
                , concat('TEL:', seo.organization_phone) as organization_phone
                , concat('FAX:', seo.organization_fax) as organization_fax
                , COALESCE(am.amount_total, 0) AS this_month_amount
                , to_char(am.invoice_date_due, 'YYYY年MM月DD日')  as invoice_date_due
                , COALESCE(pmi.previous_month_amount, 0) AS previous_month_amount
                , COALESCE(da.deposit_amount, 0) AS deposit_amount
                , COALESCE(pmb.previous_month_balance, 0) AS previous_month_balance
                , am.amount_untaxed AS this_month_purchase
                , am.amount_tax AS consumption_tax
                , concat('{str_due_date_start}','~','{str_due_date_end}','締切') as due_date
                , td.date
                , td.slip_number
                , td.detail_number
                , td.product_name
                , td.quantity
                , td.unit
                , td.unit_price
                , td.price
                , td.tax_rate
                , td.summary
                , st10.price_total_tax_rate10
                , st8.price_total_tax_rate8
                , srt8.price_total_reduced_tax_rate8
                , snt.price_total_no_tax
                , st10.tax_amount_rate10
                , st8.tax_amount_rate8
                , srt8.tax_amount_reduced_tax_rate8
                , snt.tax_amount_no_tax
                , am.amount_untaxed AS price_total
                , am.amount_tax AS price_total_tax
                , ob.payee_info
        FROM transaction_detail td
        LEFT JOIN account_move am ON td.invoice_move_id = am.id
        LEFT JOIN deposit_amount da ON am.x_organization_id = da.x_organization_id AND am.partner_id = da.partner_id
        LEFT JOIN res_partner rp ON am.partner_id = rp.id
        LEFT JOIN res_country_state rcs ON rp.state_id = rcs.id
        LEFT JOIN ss_erp_organization seo ON am.x_organization_id = seo.id
        LEFT JOIN hr_employee he ON seo.responsible_person = he.id
        LEFT JOIN res_country_state rcs2 ON seo.organization_state_id = rcs2.id
        LEFT JOIN previous_month_invoice pmi ON am.x_organization_id = pmi.x_organization_id AND am.partner_id = pmi.partner_id
        LEFT JOIN previous_month_balance pmb ON am.x_organization_id = pmb.x_organization_id AND am.partner_id = pmb.partner_id
        LEFT JOIN sum_tax_10 st10 ON st10.move_id = am.id
        LEFT JOIN sum_tax_8 st8 ON st8.move_id = am.id
        LEFT JOIN sum_reduce_tax_8 srt8 ON srt8.move_id = am.id
        LEFT JOIN sum_no_tax snt ON snt.move_id = am.id
        LEFT JOIN org_bank ob ON am.x_organization_id = ob.organization_id
        WHERE am.id = {self.id}				
        '''

        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def svf_template_export(self):

        data_send = [
            '"invoice_no","zip","address","customer_name","output_date","registration_number",' + \
            '"name","responsible_person","organization_zip","organization_address","organization_phone",' + \
            '"organization_fax","this_month_amount","invoice_date_due","previous_month_amount","deposit_amount","previous_month_balance",' + \
            '"this_month_purchase","consumption_tax","due_date","date","slip_number","detail_number","product_name","quantity","unit","unit_price",' + \
            '"price","tax_rate","summary","price_total_tax_rate10","price_total_tax_rate8","price_total_reduced_tax_rate8",' + \
            '"price_total_no_tax","tax_amount_rate10","tax_amount_rate8","tax_amount_reduced_tax_rate8","tax_amount_no_tax","price_total","price_total_tax","payee_info"']
        data_query = self._get_data_svf_r002() if not self.journal_id.x_is_construction else self._get_data_svf_r002_construction()

        if not data_query:
            raise UserError(_("出力対象のデータがありませんでした。"))

        seq_number = 1
        slip_num = data_query[0]['slip_number']
        for daq in data_query:
            one_line_data = ""
            if slip_num != daq['slip_number']:
                seq_number = 1
            slip_num = daq['slip_number']
            for da in daq:
                if daq[da] is not None:
                    if da in ['this_month_amount', 'previous_month_amount', 'deposit_amount', 'previous_month_balance',
                              'this_month_purchase', 'consumption_tax', 'price_total_tax_rate10', "price",
                              'price_total_tax_rate8', 'price_total_reduced_tax_rate8', 'price_total_no_tax',
                              'tax_amount_rate10', 'tax_amount_rate8', 'tax_amount_reduced_tax_rate8',
                              'tax_amount_no_tax', 'price_total', 'price_total_tax']:
                        one_line_data += '"' + "￥" + "{:,}".format(int(daq[da])) + '",'
                    elif da == "unit_price":
                        if int(daq[da]) == 0:
                            one_line_data += '"",'
                        else:
                            one_line_data += '"' + "{:,}".format(int(daq[da])) + '",'
                    elif da == 'detail_number':
                        one_line_data += '"' + str(seq_number) + '",'
                    else:
                        one_line_data += '"' + str(daq[da]) + '",'
                else:
                    one_line_data += '"",'
            seq_number += 1
            data_send.append(one_line_data)
        data_file = "\n".join(data_send)
        data_file = data_file[0:-1]
        return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_file, type_report='R002')

    # End Region
