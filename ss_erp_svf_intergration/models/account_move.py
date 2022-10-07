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
        registration_number = self.env['ir.config_parameter'].sudo().get_param('invoice_report.registration_number')

        now = datetime.now()

        first_day_current_month = datetime.combine(now.replace(day=1), datetime.min.time())
        last_day_current_month = datetime.combine(now.replace(day=calendar.monthrange(now.year, now.month)[1]),
                                                  datetime.max.time())

        current_date_last_month = now + relativedelta(months=-1)
        first_day_last_month = datetime.combine(current_date_last_month.replace(day=1), datetime.min.time())
        last_day_last_month = datetime.combine(current_date_last_month.replace(
            day=calendar.monthrange(current_date_last_month.year, current_date_last_month.month)[1]),
                                               datetime.max.time())

        r002_tax10_id = self.env['ir.config_parameter'].sudo().get_param('R002_tax10_id')
        r002_tax8_id = self.env['ir.config_parameter'].sudo().get_param('R002_tax8_id')
        r002_reduction_tax8_id = self.env['ir.config_parameter'].sudo().get_param('R002_reduction_tax8_id')
        r002_tax_exempt_id = self.env['ir.config_parameter'].sudo().get_param('R002_tax_exempt_id')

        if not r002_tax10_id or not r002_tax8_id or not r002_reduction_tax8_id or not r002_tax_exempt_id:
            raise UserError('パラメータで税勘定を設定してください')

        query = f'''
        with org_bank as (
        select 
            rpb.organization_id,
            concat(rb.name,rpb.x_bank_branch,rpb.x_bank_branch_number) as payee_info	
        -- 	'(',CASE When acc_type = 'bank' then '通常' ELSE '当座' END,')', rpb.acc_number）　as payee_info	
        from res_partner_bank rpb
        left join res_bank rb on rpb.bank_id = rb.id
        where rpb.organization_id is not null
        ),
        -- SUM TAX REGION
            sum_tax_10 as (
        select am.id move_id,amlat.account_tax_id tax_id, sum(quantity * price_unit) sum from account_move_line aml
        left join account_move am ON am.id = aml.move_id
        left join account_move_line_account_tax_rel amlat ON amlat.account_move_line_id = aml.id
                    where amlat.account_tax_id = '{int(r002_tax10_id)}'
                    GROUP BY am.id, amlat.account_tax_id
        ),
            sum_tax_8 as (
        select am.id move_id,amlat.account_tax_id tax_id, sum(quantity * price_unit) sum from account_move_line aml
        left join account_move am ON am.id = aml.move_id
        left join account_move_line_account_tax_rel amlat ON amlat.account_move_line_id = aml.id
                    where amlat.account_tax_id = '{int(r002_tax8_id)}'
                    GROUP BY am.id, amlat.account_tax_id
        ),
            sum_reduce_tax_8 as (
        select am.id move_id,amlat.account_tax_id tax_id, sum(quantity * price_unit ) sum from account_move_line aml
        left join account_move am ON am.id = aml.move_id
        left join account_move_line_account_tax_rel amlat ON amlat.account_move_line_id = aml.id
                    where amlat.account_tax_id = '{int(r002_reduction_tax8_id)}'
                    GROUP BY am.id, amlat.account_tax_id
        ),
            sum_no_tax as (
        select am.id move_id,amlat.account_tax_id tax_id, sum(quantity * price_unit ) sum from account_move_line aml
        left join account_move am ON am.id = aml.move_id
        left join account_move_line_account_tax_rel amlat ON amlat.account_move_line_id = aml.id
                    where amlat.account_tax_id = '{int(r002_tax_exempt_id)}'
                    GROUP BY am.id, amlat.account_tax_id
        )
        -- END

        select
         am.name as invoice_no
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
         , COALESCE(am.amount_total,0) + COALESCE(oi_pma.oi_previous_amount, 0) - COALESCE(or_pma.or_previous_amount, 0) - COALESCE(da.amount, 0) as this_month_amount -- TODO 8
         , to_char(am.invoice_date_due, 'YYYY年MM月DD日') invoice_date_due 
         , COALESCE(oi_pma.oi_previous_amount, 0) - COALESCE(or_pma.or_previous_amount, 0) as previous_month_amount
         , COALESCE(da.amount, 0) as deposit_amount
         , COALESCE(oi_pma.oi_previous_amount, 0) - COALESCE(or_pma.or_previous_amount, 0) - COALESCE(da.amount, 0) as previous_month_balance
         , COALESCE(oi_tmp.oi_tmp_amount, 0) - COALESCE(or_tmp.or_tmp_amount, 0) as this_month_purchase
         , am.amount_tax as consumption_tax
         ,  to_char(sp.date_done, 'MM/DD') as date
         , so.name as slip_number 
         , 0 as detail_number 
         , pt.name as product_name	
         , sol.product_uom_qty as quantity	
         , uu.name as unit	
         , sol.price_unit as unit_price	
         , sol.price_subtotal as price	
         , COALESCE(at.name, '') as tax_rate	
         , COALESCE(sol.x_remarks, '') as summary
         , COALESCE(st10.sum, 0) as price_total_tax_rate10
         , COALESCE(st8.sum, 0) as price_total_tax_rate8
         , COALESCE(srt8.sum, 0) as price_total_reduced_tax_rate8
         , COALESCE(snt.sum, 0) as price_total_no_tax
         , COALESCE(st10.sum * 0.1, 0) as tax_amount_rate10
         , COALESCE(st8.sum * 0.08, 0) as tax_amount_rate8
         , COALESCE(srt8.sum * 0.08, 0) as tax_amount_reduced_tax_rate8
         , 0 as tax_amount_no_tax
         -- , NULL as tax_amount_no_tax
         , COALESCE(st10.sum + st8.sum + srt8.sum + snt.sum, 0) as price_total
         , COALESCE(st10.sum * 0.1 + st8.sum * 0.08 + srt8.sum * 0.08, 0) as price_total_tax
         , ob.payee_info
         from
            account_move am  /* 仕訳 */	
            left join	
            account_move_line aml /* 仕訳項目 */	
            on am.id = aml.move_id	
            left join	
            sale_order_line_invoice_rel solir /* 販売明細と請求の関連 */	
            on aml.id = solir.invoice_line_id	
            left join	
            sale_order_line sol /* 販売オーダ明細 */	
            on solir.order_line_id = sol.id	
            left join	
            stock_picking sp /* 運送 */	
            on sol.order_id = sp.sale_id and sp.backorder_id is NULL
            left join	
            product_template pt /* プロダクトテンプレート */	
            on sol.product_id = pt.id	
            left join	
            uom_uom uu  /* 単位 */	
            on sol.product_uom = uu.id	
            left join	
            account_tax_sale_order_line_rel atsol  /* 販売オーダ明細と税の関連 */	
            on sol.id = atsol.sale_order_line_id	
            left join	
            account_tax at  /* 税 */	
            on atsol.account_tax_id = at.id	
            left join	
            sale_order so /* 販売オーダ */	
            on sol.order_id = so.id	
            left join	
            res_partner rp /* 連絡先 */	
            on am.partner_id = rp.id	
                left join 
                res_country_state rcs
                on rp.state_id = rcs.id
                left join 
                ss_erp_organization seo
                on am.x_organization_id = seo.id
                left join 
                hr_employee he
                on seo.responsible_person = he.id
                left join res_country_state rcs2
                on seo.organization_state_id = rcs2.id
                left join org_bank ob 
                on ob.organization_id = am.x_organization_id

            left join 
            ( select partner_id,x_organization_id, sum(amount_total) oi_previous_amount from account_move
            where invoice_date BETWEEN '{first_day_last_month}'
            and '{last_day_last_month}' and move_type = 'out_invoice' and state='posted'
            GROUP BY partner_id, x_organization_id
            ) oi_pma on oi_pma.partner_id = rp.id -- 10
            
            left join 
            ( select partner_id,x_organization_id, sum(amount_total) or_previous_amount from account_move
            where invoice_date BETWEEN '{first_day_last_month}' 
            and '{last_day_last_month}' and move_type = 'out_refund'
            GROUP BY partner_id, x_organization_id
            ) or_pma on or_pma.partner_id = am.partner_id and or_pma.x_organization_id = am.x_organization_id -- 10
            
            left join 
            ( select da_ap.partner_id,da_ap.x_organization_id, sum(da_ap.amount) amount from account_payment da_ap
            left join account_move da_jour on da_jour.id = da_ap.move_id
            where da_jour.date BETWEEN '{first_day_current_month}' 
            and '{last_day_current_month}' and move_type = 'out_refund'
            GROUP BY da_ap.partner_id, da_ap.x_organization_id
            ) da on da.partner_id = am.partner_id and da.x_organization_id = am.x_organization_id -- 11
            
            left join 
            ( select partner_id,x_organization_id, sum(amount_total) oi_tmp_amount from account_move
            where invoice_date BETWEEN '{first_day_current_month}' 
            and '{last_day_current_month}' and move_type = 'out_invoice'
            GROUP BY partner_id, x_organization_id
            ) oi_tmp on oi_tmp.partner_id = am.partner_id and oi_tmp.x_organization_id = am.x_organization_id --13
            
            left join 
            ( select partner_id,x_organization_id, sum(amount_total) or_tmp_amount from account_move
            where invoice_date BETWEEN '{first_day_current_month}'
            and '{last_day_current_month}' and move_type = 'out_refund'
            GROUP BY partner_id, x_organization_id
            ) or_tmp on or_tmp.partner_id = am.partner_id and or_tmp.x_organization_id = am.x_organization_id -- 13
            
            left join sum_tax_10 st10
            on st10.move_id = am.id
            left join sum_tax_8 st8
            on st8.move_id = am.id
            left join sum_reduce_tax_8 srt8
            on srt8.move_id = am.id
            left join sum_no_tax snt
            on snt.move_id = am.id
            
        where sp.state = 'done' and am.id = '{self.id}'
        order by
                am.name,
                so.name,
            sol.product_id 	
            , to_char(sp.date_done, 'MM/DD') 	             	
        '''
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def svf_template_export(self):

        data_send = [
            '''"invoice_no","zip","address","customer_name","output_date","registration_number","name","responsible_person","organization_zip","organization_address","organization_phone","organization_fax","this_month_amount","invoice_date_due","previous_month_amount","deposit_amount","previous_month_balance","this_month_purchase","consumption_tax","date","slip_number","detail_number","product_name","quantity","unit","unit_price","price","tax_rate","summary","price_total_tax_rate10","price_total_tax_rate8","price_total_reduced_tax_rate8","price_total_no_tax","tax_amount_rate10","tax_amount_rate8","tax_amount_reduced_tax_rate8","tax_amount_no_tax","price_total","price_total_tax","payee_info"''']
        #
        # # data_file = '''"invoice_no","zip","address","customer_name","output_date","registration_number","name","responsible_person","organization_zip","organization_address","organization_phone","organization_fax","this_month_amount","invoice_date_due","previous_month_amount","deposit_amount","previous_month_balance","this_month_purchase","consumption_tax","date","slip_number","detail_number","product_name","quantity","unit","unit_price","price","tax_rate","summary","price_total_tax_rate10","price_total_tax_rate8","price_total_reduced_tax_rate8","price_total_no_tax","tax_amount_rate10","tax_amount_rate8","tax_amount_reduced_tax_rate8","tax_amount_no_tax","price_total","price_total_tax","payee_info"
        # # "1234567890","〒060-0010","札幌市中央区９条西２１丁目１番地１１号","大槻食材株式会社　札幌店　様","2020年9月20日","T1234567890123","山陰酸素工業　出雲支店","支店長：山陰　太郎","〒693-0043","2020年9月20日　現在","TEL：0853-28-2866","FAX：0853-28-2870","\3,712,740","2021年10月31日","\100,000","\100,000","\0","\3,404,451","\308,289","10/31","000001","00001","振込","","","","100,000","","","1,796,645","0","1,607,806","0","179,663","0","128,624","0","3,404,451","308,289","山陰合同銀行出雲支店（当座）1002529"
        # # "1234567890","〒060-0010","札幌市中央区９条西２１丁目１番地１１号","大槻食材株式会社　札幌店　様","2020年9月20日","T1234567890123","山陰酸素工業　出雲支店","支店長：山陰　太郎","〒693-0043","2020年9月20日　現在","TEL：0853-28-2866","FAX：0853-28-2870","\3,712,740","2021年10月31日","\100,000","\100,000","\0","\3,404,451","\308,289","10/31","000001","00001","現金","","","","200,000","","","1,796,645","0","1,607,806","0","179,663","0","128,624","0","3,404,451","308,289","山陰合同銀行出雲支店（当座）1002529"
        # # "1234567890","〒060-0010","札幌市中央区９条西２１丁目１番地１１号","大槻食材株式会社　札幌店　様","2020年9月20日","T1234567890123","山陰酸素工業　出雲支店","支店長：山陰　太郎","〒693-0043","2020年9月20日　現在","TEL：0853-28-2866","FAX：0853-28-2870","\3,712,740","2021年10月31日","\100,000","\100,000","\0","\3,404,451","\308,289","","","","*** 入　金　計 ***","","","","300,000","","","1,796,645","0","1,607,806","0","179,663","0","128,624","0","3,404,451","308,289","山陰合同銀行出雲支店（当座）1002529"
        # # "1234567890","〒060-0010","札幌市中央区９条西２１丁目１番地１１号","大槻食材株式会社　札幌店　様","2020年9月20日","T1234567890123","山陰酸素工業　出雲支店","支店長：山陰　太郎","〒693-0043","2020年9月20日　現在","TEL：0853-28-2866","FAX：0853-28-2870","\3,712,740","2021年10月31日","\100,000","\100,000","\0","\3,404,451","\308,289","10/3","000002","00002","プロパン／サプライ","9,992.10","Kg","112.80","1,127,109","課税10%","配送センター991","1,796,645","0","1,607,806","0","179,663","0","128,624","0","3,404,451","308,289","山陰合同銀行出雲支店（当座）1002529"
        # # "1234567890","〒060-0010","札幌市中央区９条西２１丁目１番地１１号","大槻食材株式会社　札幌店　様","2020年9月20日","T1234567890123","山陰酸素工業　出雲支店","支店長：山陰　太郎","〒693-0043","2020年9月20日　現在","TEL：0853-28-2866","FAX：0853-28-2870","\3,712,740","2021年10月31日","\100,000","\100,000","\0","\3,404,451","\308,289","10/8","000003","00003","プロパン／サプライ","2,295.00","ｍ3","225.60","517,752","課税10%","配送センター991","1,796,645","0","1,607,806","0","179,663","0","128,624","0","3,404,451","308,289","山陰合同銀行出雲支店（当座）1002529"
        # # "1234567890","〒060-0010","札幌市中央区９条西２１丁目１番地１１号","大槻食材株式会社　札幌店　様","2020年9月20日","T1234567890123","山陰酸素工業　出雲支店","支店長：山陰　太郎","〒693-0043","2020年9月20日　現在","TEL：0853-28-2866","FAX：0853-28-2870","\3,712,740","2021年10月31日","\100,000","\100,000","\0","\3,404,451","\308,289","10/10","000004","00004","プロパン／サプライ","345.60","Kg","112.80","38,984","課税10%","配送センター991","1,796,645","0","1,607,806","0","179,663","0","128,624","0","3,404,451","308,289","山陰合同銀行出雲支店（当座）1002529"
        # # '''
        #
        # # 詳細（入金）Payment Data  16,17(1)
        # payment_data_1 = payment_record.date.strftime(
        #     "%Y年%m月%d日") + payment_record.name + "" + payment_record.x_receipt_type + "" + "" + "" + "{:,}".format(
        #     int(payment_record.amount)) + "" + ""
        #
        # # ＜入金小計＞ 16,17(2)
        # payment_data_2 = "" + "" + "" + "" + "" + "" + "{:,}".format(int(payment_record.amount)) + "" + ""
        #
        # # for so in so_records:
        # #     picking_records = so.picking_ids
        # #     for pic in picking_records:
        # #         mov_line = pic.move_line_ids
        # #         for ml in mov_line:
        # #             am_data = ml.move_id.date.strftime("%Y年%m月%d日") + ml.move_id.name + '' + ml.product_id.name
        #
        # for so in so_records:
        #     for line in so.order_line:
        #         for sm in line.move_ids:
        #             # ＜請求明細＞ 16,17(3)
        #             product_detail_data_1 = sm.date.strftime(
        #                 "%Y年%m月%d日") + sm.name + '' + line.product_id.name + line.product_uom_qty + line.product_uom_id.name + line.price_unit + line.price_subtotal + line.tax_id.name + line.x_remarks
        #             data_send.append(product_detail_data_1)
        #
        #             # ＜請求明細＞ 16,17(4)
        #             product_detail_data_2 = sm.date.strftime(
        #                 "%Y年%m月%d日") + sm.name + '' + line.product_id.name + line.product_uom_qty + line.product_uom_id.name + line.price_unit + line.price_subtotal + line.tax_id.name + line.x_remarks
        #             data_send.append(product_detail_data_1)
        #
        # r002_svf_registration_number = self.env['ir.config_parameter'].sudo().get_param(
        #     'invoice_report.registration_number')
        # for so in so_records:
        #     customer_address = so.partner_invoice_id.street + '' if so.partner_invoice_id.street else ''
        #     customer_address += so.partner_invoice_id.street2 + '' if so.partner_invoice_id.street2 else ''
        #     customer_address += so.partner_invoice_id.city + '' if so.partner_invoice_id.city else ''
        #     customer_address += so.partner_invoice_id.state_id.name + '' if so.partner_invoice_id.state_id.name else ''
        #     customer_address += so.partner_invoice_id.country_id.name + '' if so.partner_invoice_id.country_id.name else ''
        #
        #     organization_address = self.x_organization_id.organization_state_id.name + '' if self.x_organization_id.organization_state_id.name else ''
        #     organization_address += self.x_organization_id.organization_city + '' if self.x_organization_id.organization_city else ''
        #     organization_address += self.x_organization_id.organization_street + '' if self.x_organization_id.organization_street else ''
        #     organization_address += self.x_organization_id.organization_street2 + '' if self.x_organization_id.organization_street2 else ''
        #
        #     output_date = fields.Datetime.now().strftime("%Y年%m月%d日")
        #     invoice_data = ['"' + self.name, so.partner_invoice_id.zip, customer_address,
        #                     so.partner_invoice_id.name + '様', output_date, r002_svf_registration_number,
        #                     self.x_organization_id.name, self.x_organization_id.organization_zip, organization_address,
        #                     self.x_organization_id.organization_fax, '下記の通りご請求申し上げます。', 'x' + '"']
        #
        # data_send.append(payment_data_1)
        # data_file = "\n".join(data_send)

        # *** use query in file design :))****
        data_query = self._get_data_svf_r002()
        if not data_query:
            raise UserError(_("出力対象のデータがありませんでした。"))

        seq_number = 1
        for daq in data_query:
            one_line_data = ""
            for da in daq:
                if da is not None:
                    if da in ['this_month_amount', 'previous_month_amount', 'deposit_amount', 'previous_month_balance', 'this_month_purchase', 'consumption_tax']:
                        one_line_data += '"' + "￥" + "{:,}".format(int(daq[da])) + '",'
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
