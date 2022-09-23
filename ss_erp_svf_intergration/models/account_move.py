# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import requests
import base64
import json


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_data_svf_r002(self):

        query = f''' select 						
                         a.name as 請求書NO						
                         , to_char(now(), 'YYYY年MM月DD日')  as 発行日						
                         , o.zip as 顧客／郵便番号						
                         , p.name as 顧客／都道府県						
                         , o.city as 顧客／市区町村						
                         , o.street as 顧客／町名番地						
                         , o.street2 as 顧客／町名番地２						
                         , o.name as 顧客名						
                         , l.complete_name as 支店名						
                         , n.name as 責任者						
                         , l.organization_zip as 支店郵便番号						
                         , m.name as 支店住所／都道府県						
                         , l.organization_city as 支店住所／市区町村						
                         , l.organization_street as 支店住所／町名番地						
                         , l.organization_street2 as 支店住所／町名番地２						
                         , l.organization_phone as 支店TEL						
                         , l.organization_fax as 支店FAX						
                         , r.name as 銀行名						
                         , q.x_bank_branch as 銀行支店名						
                         , q.acc_number as 口座番号						
                         ,  to_char(e.date_done, 'MM/DD') as 日付						
                         , k.name as 伝票番号						
                         , g.name as 商品名						
                         , null as 規格・商品名						
                         , d.product_uom_qty as 数量						
                         , h.name as 単位						
                         , d.price_unit as 単価						
                         , d.price_subtotal as 本体価格						
                         , j.name as 税率						
                         , d.x_remarks as 適用						
                        from						
                            account_move a  /* 仕訳 */						
                            inner join						
                            account_move_line b /* 仕訳項目 */						
                            on a.id = b.move_id						
                            inner join						
                            sale_order_line_invoice_rel c /* 販売明細と請求の関連 */						
                            on b.id = c.invoice_line_id						
                            inner join						
                            sale_order_line d /* 販売オーダ明細 */						
                            on c.order_line_id = d.id						
                            inner join						
                            stock_picking e /* 運送 */						
                            on d.order_id = e.sale_id						
                            inner join						
                            product_template g /* プロダクトテンプレート */						
                            on d.product_id = g.id						
                            inner join						
                            uom_uom h  /* 単位 */						
                            on d.product_uom = h.id						
                            inner join						
                            account_tax_sale_order_line_rel i  /* 販売オーダ明細と税の関連 */						
                            on d.id = i.sale_order_line_id						
                            inner join						
                            account_tax j  /* 税 */						
                            on i.account_tax_id = j.id						
                            inner join						
                            sale_order k /* 販売オーダ */						
                            on d.order_id = k.id						
                            inner join  						
                            ss_erp_organization l  /* 組織 */						
                            on k.x_organization_id = l.id						
                            inner join						
                            res_country_state m /* 都道府県（組織） */						
                            on l.organization_state_id = m.id						
                            inner join						
                            hr_employee n /* 従業員 */						
                            on l.responsible_person = n.id						
                            inner join						
                            res_partner o /* 連絡先 */						
                            on k.partner_id = o.id						
                            inner join						
                            res_country_state p /* 都道府県（得意先） */						
                            on o.state_id = p.id						
                            inner join						
                            res_partner_bank q /* 銀行口座 */						
                            on l.id = q.organization_id						
                            inner join						
                            res_bank r /* 銀行 */						
                            on q.bank_id = r.id						
                        where						
                            a.id = '{self.id}'					
                        order by						
                            d.product_id 						
                            , to_char(e.date_done, 'MM/DD') 						
                            , k.name						
                        ;'''
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
            for da in daq.values():
                one_line_data += '"' + str(da) + '",'
            data_send.append(one_line_data)
        data_file = "\n".join(data_send)
        data_file = data_file[0:-1]
        return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_file, type_report='R002')

    # End Region
