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

        # query = f''' select
        #                  a.name as 請求書NO
        #                  , to_char(now(), 'YYYY年MM月DD日')  as 発行日
        #                  , o.zip as 顧客／郵便番号
        #                  , p.name as 顧客／都道府県
        #                  , o.city as 顧客／市区町村
        #                  , o.street as 顧客／町名番地
        #                  , o.street2 as 顧客／町名番地２
        #                  , o.name as 顧客名
        #                  , l.complete_name as 支店名
        #                  , n.name as 責任者
        #                  , l.organization_zip as 支店郵便番号
        #                  , m.name as 支店住所／都道府県
        #                  , l.organization_city as 支店住所／市区町村
        #                  , l.organization_street as 支店住所／町名番地
        #                  , l.organization_street2 as 支店住所／町名番地２
        #                  , l.organization_phone as 支店TEL
        #                  , l.organization_fax as 支店FAX
        #                  , r.name as 銀行名
        #                  , q.x_bank_branch as 銀行支店名
        #                  , q.acc_number as 口座番号
        #                  ,  to_char(e.date_done, 'MM/DD') as 日付
        #                  , k.name as 伝票番号
        #                  , g.name as 商品名
        #                  , null as 規格・商品名
        #                  , d.product_uom_qty as 数量
        #                  , h.name as 単位
        #                  , d.price_unit as 単価
        #                  , d.price_subtotal as 本体価格
        #                  , j.name as 税率
        #                  , d.x_remarks as 適用
        #                 from
        #                     account_move a  /* 仕訳 */
        #                     inner join
        #                     account_move_line b /* 仕訳項目 */
        #                     on a.id = b.move_id
        #                     inner join
        #                     sale_order_line_invoice_rel c /* 販売明細と請求の関連 */
        #                     on b.id = c.invoice_line_id
        #                     inner join
        #                     sale_order_line d /* 販売オーダ明細 */
        #                     on c.order_line_id = d.id
        #                     inner join
        #                     stock_picking e /* 運送 */
        #                     on d.order_id = e.sale_id
        #                     inner join
        #                     product_template g /* プロダクトテンプレート */
        #                     on d.product_id = g.id
        #                     inner join
        #                     uom_uom h  /* 単位 */
        #                     on d.product_uom = h.id
        #                     inner join
        #                     account_tax_sale_order_line_rel i  /* 販売オーダ明細と税の関連 */
        #                     on d.id = i.sale_order_line_id
        #                     inner join
        #                     account_tax j  /* 税 */
        #                     on i.account_tax_id = j.id
        #                     inner join
        #                     sale_order k /* 販売オーダ */
        #                     on d.order_id = k.id
        #                     inner join
        #                     ss_erp_organization l  /* 組織 */
        #                     on k.x_organization_id = l.id
        #                     inner join
        #                     res_country_state m /* 都道府県（組織） */
        #                     on l.organization_state_id = m.id
        #                     inner join
        #                     hr_employee n /* 従業員 */
        #                     on l.responsible_person = n.id
        #                     inner join
        #                     res_partner o /* 連絡先 */
        #                     on k.partner_id = o.id
        #                     inner join
        #                     res_country_state p /* 都道府県（得意先） */
        #                     on o.state_id = p.id
        #                     inner join
        #                     res_partner_bank q /* 銀行口座 */
        #                     on l.id = q.organization_id
        #                     inner join
        #                     res_bank r /* 銀行 */
        #                     on q.bank_id = r.id
        #                 where
        #                     a.id = '{self.id}'
        #                 order by
        #                     d.product_id
        #                     , to_char(e.date_done, 'MM/DD')
        #                     , k.name
        #                 ;'''

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

        query = f'''
        with org_bank as (
        select 
            rpb.organization_id,
            concat(rb.name,rpb.x_bank_branch,rpb.x_bank_branch_number) as payee_info	
        -- 	'(',CASE When acc_type = 'bank' then '通常' ELSE '当座' END,')', rpb.acc_number）　as payee_info	
        from res_partner_bank rpb
        left join res_bank rb on rpb.bank_id = rb.id
        where rpb.organization_id is not null
        )
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
         , am.invoice_date_due 
         , COALESCE(oi_pma.oi_previous_amount, 0) - COALESCE(or_pma.or_previous_amount, 0) as previous_month_amount
         , COALESCE(da.amount, 0) as deposit_amount
         , COALESCE(oi_pma.oi_previous_amount, 0) - COALESCE(or_pma.or_previous_amount, 0) - COALESCE(da.amount, 0) as previous_month_balance
         , COALESCE(oi_tmp.oi_tmp_amount, 0) - COALESCE(or_tmp.or_tmp_amount, 0) as this_month_purchase
         , am.amount_tax as consumption_tax
         ,  to_char(sp.date_done, 'MM/DD') as date
         , so.name as slip_number 
         , so.name as detail_number 
         , pt.name as product_name	
         , null as 規格・商品名	
         , sol.product_uom_qty as quantity	
         , uu.name as unit	
         , sol.price_unit as unit_price	
         , sol.price_subtotal as price	
         , at.name as tax_rate	
         , sol.x_remarks as summary
         , NULL as price_total_tax_rate10
         , NULL as price_total_tax_rate8
         , NULL as price_total_reduced_tax_rate8
         , NULL as price_total_no_tax
         , NULL as tax_amount_rate10
         , NULL as tax_amount_rate8
         , NULL as tax_amount_reduced_tax_rate8
         , NULL as tax_amount_no_tax
         , NULL as tax_amount_no_tax
         , NULL as price_total
         , NULL as price_total_tax
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
            on sol.order_id = sp.sale_id	
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
            ( select partner_id, sum(amount_total) oi_previous_amount from account_move
            where invoice_date BETWEEN '{first_day_last_month}'
            and '{last_day_last_month}' and move_type = 'out_invoice'
            GROUP BY partner_id
            ) oi_pma on oi_pma.partner_id = rp.id -- 10
            
            left join 
            ( select partner_id, sum(amount_total) or_previous_amount from account_move
            where invoice_date BETWEEN '{first_day_last_month}' 
            and '{last_day_last_month}' and move_type = 'out_refund'
            GROUP BY partner_id
            ) or_pma on or_pma.partner_id = rp.id -- 10
            
            left join 
            ( select da_ap.partner_id, sum(da_ap.amount) amount from account_payment da_ap
            left join account_move da_jour on da_jour.id = da_ap.move_id
            where da_jour.date BETWEEN '{first_day_current_month}' 
            and '{last_day_current_month}' and move_type = 'out_refund'
            GROUP BY da_ap.partner_id
            ) da on da.partner_id = rp.id -- 11
            
            left join 
            ( select partner_id, sum(amount_total) oi_tmp_amount from account_move
            where invoice_date BETWEEN '{first_day_current_month}' 
            and '{last_day_current_month}' and move_type = 'out_invoice'
            GROUP BY partner_id
            ) oi_tmp on oi_tmp.partner_id = rp.id -- 13
            
            left join 
            ( select partner_id, sum(amount_total) or_tmp_amount from account_move
            where invoice_date BETWEEN '{first_day_current_month}'
            and '{last_day_current_month}' and move_type = 'out_refund'
            GROUP BY partner_id
            ) or_tmp on or_tmp.partner_id = rp.id -- 13
        where sp.state = 'done' and am.id = '{self.id}'
        order by
                am.name,
            sol.product_id 	
            , to_char(sp.date_done, 'MM/DD') 	
            , so.name	
        '''
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def svf_template_export(self):

        # Prepare data sent to SVF
        # customer_so_recs = self.env['sale.order'].search([('state', 'not in', ['draft', 'cancel'])])
        # so_records = customer_so_recs.filtered(lambda csr: self.id in csr.invoice_ids.ids)
        # if not so_records:
        #     raise UserError('対応する SO レコードが見つかりません。')
        #
        # customer_payment_recs = self.env['account.payment'].search(
        #     [('state', '=', 'posted'), ('reconciled_invoice_ids', '!=', []), ])
        # payment_record = customer_payment_recs.filtered(lambda cpr: self.id in cpr.reconciled_invoice_ids.ids)
        # if not payment_record:
        #     raise UserError('対応する Payment レコードが見つかりません。')
        #
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

        for daq in data_query:
            one_line_data = ""
            for da in daq:
                if da is not None:
                    if da in ['this_month_amount', 'previous_month_amount', 'deposit_amount', 'previous_month_balance', 'this_month_purchase', 'consumption_tax']:
                        one_line_data += '"' + "￥" + "{:,}".format(int(daq[da])) + '",'
                    else:
                        one_line_data += '"' + str(daq[da]) + '",'
                else:
                    one_line_data += '"",'
            data_send.append(one_line_data)
        data_file = "\n".join(data_send)
        data_file = data_file[0:-1]
        return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_file, type_report='R002')

    # End Region
