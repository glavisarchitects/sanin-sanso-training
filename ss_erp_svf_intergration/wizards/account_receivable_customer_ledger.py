# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json
from datetime import date, timedelta, datetime
from odoo.fields import Date, Datetime


class AccountReceivableCustomerLedger(models.TransientModel):
    _name = 'account.receivable.customer.ledger'

    due_date_start = fields.Date(string='期日（開始）')
    due_date_end = fields.Date(string='期日（終了）')

    # form/Sample/ga_test/
    def svf_template_export(self):
        data_file = self._prepare_data_file()
        # data_file = '''"得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10100000","大和設備株式会社","11/20","000009","","**  入　金  **","","他支店入金","","","82,582","","","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10100000","大和設備株式会社","11/20","000009","","**  入　金  **","","振込手数料","","","110","","","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10100000","大和設備株式会社","","","","＜　入　金　計　＞","","","","","82,692","","","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10100000","大和設備株式会社","11/04","432145","06841101","フロン　R４０７CーNRC　１０KG","","","1.00 本","12,800.00","12,800","","","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10100000","大和設備株式会社","","","","**　フロン　R４０７CーNRC　１０KG　計　**","","","1.0 個","","12,800","","","","","松本様"
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10100000","大和設備株式会社","","","","＜　[フロン]　＞","","","1.0 kg","","12,800","","←パナソニック産機システムズ株式会社　修繕・点検","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10100000","大和設備株式会社","11/30","436786","60300003301","菅沢ダム様暖房前GHP簡易点検","直送","","1.00 式","35,000.00","35,000","","","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10100000","大和設備株式会社","","","","**　菅沢ダム様暖房前GHP簡易点検　計　**","","","1.0 式","","35,000","","","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10100000","大和設備株式会社","11/30","436784","6030010365","菅沢ダム様PAC-1系統修繕費","直送","","1.00 式","105,000.00","105,000","","←パナソニック産機システムズ株式会社　修繕・点検","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10100000","大和設備株式会社","","","","**　菅沢ダム様PAC-1系統修繕費　計　**","","","1.0 式","","105,000","","","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10100000","大和設備株式会社","","","","＜　[器材／サービス]　＞","","","2.0","","140,000","","","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10100000","大和設備株式会社","","","　","**　合　計　**","","","","","152,800","","","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10170000","フジッコ株式会社　境港工場","11/20","000009","","**  入　金  **","","他支店入金","","","350,422","","","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10170000","フジッコ株式会社　境港工場","11/20","000009","","**  入　金  **","","振込手数料","","","880","","","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10170000","フジッコ株式会社　境港工場","","","","＜　入　金　計　＞","","","","","351,302","","","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10170000","フジッコ株式会社　境港工場","11/02","429363","F125","食品添加物液化窒素　ＬＧＣ","","","107.00 m3","190.00","20,330","","","*8%","","326017840"
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10170000","フジッコ株式会社　境港工場","11/04","429646","F125","食品添加物液化窒素　ＬＧＣ","","","107.00 m3","190.00","20,330","","","*8%","","326017856"
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10170000","フジッコ株式会社　境港工場","11/06","429930","F125","食品添加物液化窒素　ＬＧＣ","","","214.00 m3","190.00","40,660","","","*8%","","326017890"
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10170000","フジッコ株式会社　境港工場","11/10","430608","F125","食品添加物液化窒素　ＬＧＣ","","","214.00 m3","190.00","40,660","","","*8%","","326017944"
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10170000","フジッコ株式会社　境港工場","11/12","431025","F125","食品添加物液化窒素　ＬＧＣ","","","214.00 m3","190.00","40,660","","","*8%","","326017993"
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10170000","フジッコ株式会社　境港工場","11/16","431548","F125","食品添加物液化窒素　ＬＧＣ","","","214.00 m3","190.00","40,660","","","*8%","","321013065"
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10170000","フジッコ株式会社　境港工場","11/18","432228","F125","食品添加物液化窒素　ＬＧＣ","","","107.00 m3","190.00","20,330","","","*8%","","321013088"
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10170000","フジッコ株式会社　境港工場","11/24","433597","F125","食品添加物液化窒素　ＬＧＣ","","","107.00 m3","190.00","20,330","","","*8%","","321013137"
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10170000","フジッコ株式会社　境港工場","11/26","434520","F125","食品添加物液化窒素　ＬＧＣ","","","107.00 m3","190.00","20,330","","","*8%","","321013179"
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10170000","フジッコ株式会社　境港工場","","","","**　食品添加物液化窒素　ＬＧＣ　計　**","","","1,391.0 m3","","264,290","","","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10170000","フジッコ株式会社　境港工場","","","","＜　[窒素]　＞","","","1,391.0 m3","","264,290","","","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10170000","フジッコ株式会社　境港工場","","","","**　合　計　**","","","","","264,290","","","","",""
        #             "得意先元帳（商品順）","2022年12月05日 09:30:51","2022年11月01日","2020年11月30日","03000","米子支店","10170000","フジッコ株式会社　境港工場","","","","**　総　合　計　**","","","","","205,605,853","","","","",""'''
        return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_file, type_report='R004')

    # 請求書一覧表出力ボタンを追加する。
    def create_accounts_receivable_ledger(self):
        return self.svf_template_export()

    def _get_branch_of_login_user(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id.organization_first
        else:
            return False

    def _get_account_receivable_balance(self):
        branch = self._get_branch_of_login_user()
        title = "得意先元帳（商品順）"
        due_date_start = datetime.combine(self.due_date_start, datetime.min.time())
        due_date_end = datetime.combine(self.due_date_end, datetime.max.time())

        str_due_date_start = due_date_start.strftime("%Y年%m月%d日")
        str_due_date_end = due_date_end.strftime("%Y年%m月%d日")

        query = f''' 

            -- nyukin
            -- nyukin detail
            With nyukin as ((select 
                1 as order_sequence,
                am.x_organization_id,
                ap.partner_id,
                rp.ref as customer_code,
                rp.name as customer_name,
                am.date, 	
                am.name as slip_number, 
                '**  入　金  **' as product_name,
                aj.name as line_division_name, 
                ap.amount
            from account_payment ap
            left join account_move am on ap.move_id = am.id
            left join account_journal aj on am.journal_id = aj.id
            left join res_partner rp on rp.id = ap.partner_id
            where ap.payment_type = 'inbound' and am.date <= '{self.due_date_end}' and am.date >= '{self.due_date_start}'
            and ap.partner_id is not null
            order by ap.partner_id, am.date)
            union all 
            -- nyukin sum
            (select 
                2,
                am.x_organization_id,
                ap.partner_id,
                rp.ref as customer_code,
                rp.name as customer_name,
                NULL,
                NULL,
                '＜　入　金　計　＞' as product_name,
                NULL,
                sum(ap.amount)
            from account_payment ap
            left join account_move am on ap.move_id = am.id
            left join res_partner rp on rp.id = ap.partner_id
            where ap.payment_type = 'inbound' and am.date <= '{self.due_date_end}' and am.date >= '{self.due_date_start}'
            and ap.partner_id is not null
            GROUP BY ap.partner_id, rp.name, am.x_organization_id,rp.ref
            )
            ORDER BY partner_id, order_sequence), delivery as (
            select 
                sml.date::TIMESTAMP::DATE as date,
                sp.x_organization_id,
                sp.name as slip_number,
                sp.sale_id,
                sp.partner_id,
                rp.ref as customer_code,
                rp.name as customer_name,
                sml.product_id,
                uu.name as measure,
                pt.default_code as product_code,
                pt.name as product_name,
                pm.name as medium_class,
                case 
                    when spt.code = 'outgoing' then sml.qty_done 
                    when spt.code = 'incoming' then -sml.qty_done else 0 end as quantity,
                tb1.price_unit as unit_price,
                case 
                    when spt.code = 'outgoing' then sml.qty_done * tb1.price_unit 
                    when spt.code = 'incoming' then -sml.qty_done * tb1.price_unit else 0 end as amount_of_money

            from stock_move_line sml
            left join stock_move sm on sm.id = sml.move_id
            left join stock_picking sp on sm.picking_id = sp.id
            left join stock_picking_type spt on sp.picking_type_id = spt.id
            left join product_product pp on sm.product_id = pp.id
            left join product_template pt on pp.product_tmpl_id = pt.id
            left join uom_uom uu on sml.product_uom_id = uu.id
            left join ss_erp_product_medium_classification pm on pt.x_medium_classification_id = pm.id
            left join res_partner rp on sp.partner_id = rp.id
            left join 
            (select sol.product_id, sol.price_unit,sol.order_id from sale_order_line sol left join sale_order so on sol.order_id = so.id) tb1 on sp.sale_id = tb1.order_id and tb1.product_id = sml.product_id
            where sml.state = 'done' and sp.sale_id is not null and sml.date <= '{self.due_date_end}' and sml.date >= '{self.due_date_start}'
            )
            select 
            '{title}' as title,
            to_char(now(), 'YYYY年MM月DD日 HH24:MI:SS') as output_date,
            '{str_due_date_start}' as due_date_start,
            '{str_due_date_end}' as due_date_end,
            seo.organization_code as branch_code,
            seo.name as branch_name,
            all_tb.customer_code,
            all_tb.customer_name,
            all_tb.date,
            all_tb.slip_number,
            all_tb.product_id,
            all_tb.medium_class,
            all_tb.product_code,
            all_tb.product_name,
            NULL as data_name,		
            all_tb.line_division_name,
            all_tb.quantity,
            all_tb.unit_price,
            all_tb.amount_of_money,            
            NULL as destination_name,
            NULL as drop_shipping_name,
            NULL as taxation,
            NULL as order_number,
            NULL as comment,
            all_tb.order_sequence
            from
            (
                select 
                    nyukin.order_sequence,
                    nyukin.x_organization_id,
                    nyukin.partner_id,
                    nyukin.customer_code,
                    nyukin.customer_name,
                    to_char(nyukin.date, 'MM/DD') as date,
                    nyukin.slip_number,
                    NULL as product_id,
                    NULL as medium_class,
                    NULL as product_code,
                    nyukin.product_name,		
                    nyukin.line_division_name,
                    NULL as quantity,
                    NULL as unit_price,
                    nyukin.amount as amount_of_money,
                    NULL sub_seq
                from nyukin
            union all
                select 
                    3,
                    delivery.partner_id,
                    delivery.x_organization_id,
                    delivery.customer_code,
                    delivery.customer_name,
                    to_char(delivery.date, 'MM/DD'),
                    delivery.slip_number,
                    delivery.product_id,
                    delivery.medium_class,
                    delivery.product_code,
                    delivery.product_name,
                    NULL,
                    CONCAT(to_char(delivery.quantity,'999'),' ', delivery.measure),
                    delivery.unit_price,
                    delivery.amount_of_money,
                    1
                FROM delivery
            union all 
                select 
                    3,
                    delivery.partner_id,
                    delivery.x_organization_id,
                    delivery.customer_code,
                    delivery.customer_name,
                    NULL,
                    NULL,
                    delivery.product_id,
                    delivery.medium_class,
                    NULL,
                    CONCAT  ('**　', delivery.product_name, '　計　**'),
                    NULL,
                    CONCAT(to_char(sum(delivery.quantity),'999'),' ', delivery.measure),
                    NULL,
                    SUM(delivery.amount_of_money),
                    2		
                FROM delivery
                GROUP BY 	delivery.partner_id,delivery.x_organization_id,
                    delivery.customer_code,delivery.measure,delivery.product_id,
                    delivery.customer_name,delivery.medium_class,delivery.product_name
            union all 
                select 
                    5,
                    delivery.partner_id,
                    delivery.x_organization_id,
                    delivery.customer_code,
                    delivery.customer_name,
                    NULL,
                    NULL,
                    NULL,
                    delivery.medium_class,
                    NULL,
                    CONCAT  ('＜　[', delivery.medium_class, ']　＞'),
                    NULL,
                    to_char(sum(delivery.quantity),'999'),
                    NULL,
                    SUM(delivery.amount_of_money),
                    NULL
                FROM delivery
                GROUP BY 	delivery.partner_id,delivery.x_organization_id,
                    delivery.customer_code,
                    delivery.customer_name,delivery.medium_class
            union all 
                select 
                    6,
                    delivery.partner_id,
                    delivery.x_organization_id,
                    delivery.customer_code,
                    delivery.customer_name,
                    NULL,
                    NULL,
                    NULL,
                    delivery.medium_class,
                    NULL,
                    '**　合　計　**',
                    NULL,
                    NULL,
                    NULL,
                    SUM(delivery.amount_of_money),
                    NULL
                FROM delivery
                GROUP BY 	delivery.partner_id,delivery.x_organization_id,
                    delivery.customer_code,delivery.medium_class,
                    delivery.customer_name           
            ) all_tb
            left join ss_erp_organization seo on all_tb.x_organization_id = seo.id
            where all_tb.x_organization_id = '{branch.id}'
            Order by all_tb.x_organization_id, all_tb.partner_id,all_tb.order_sequence, all_tb.product_id, all_tb.sub_seq '''
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def _prepare_data_file(self):
        # ヘッダ
        new_data = [
            '"title","output_date","due_date_start","due_date_end","branch_code",' + \
            '"branch_name","customer_code","customer_name","date","slip_number",' + \
            '"product_code","product_name","data_name","line_division_name",' + \
            '"quantity","unit_price","amount_of_money","destination_name","drop_shipping_name","taxation","order_number","comment"']

        total_amount = 0
        account_receivable_balance = self._get_account_receivable_balance()

        if not account_receivable_balance:
            raise UserError(_("出力対象のデータがありませんでした。"))

        if account_receivable_balance is not None:
            for row in account_receivable_balance:
                data_line = ""
                for col in row:
                    if row[col] is not None:
                        if col in ['unit_price', 'amount_of_money']:
                            data_line += '"' + "{:,}".format(int(row[col])) + '",'
                        else:
                            if col != 'order_sequence':
                                data_line += '"' + str(row[col]) + '",'
                            else:
                                total_amount += int(row['amount_of_money'])
                    else:
                        data_line += '"",'
                new_data.append(data_line)

            last_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
                account_receivable_balance[0]['title'],
                account_receivable_balance[0]['output_date'],
                account_receivable_balance[0]['due_date_start'],
                account_receivable_balance[0]['due_date_end'],
                account_receivable_balance[0]['branch_code'],
                account_receivable_balance[0]['branch_name'],
                account_receivable_balance[0]['customer_code'],
                account_receivable_balance[0]['customer_name'],
                '',
                '',
                '',
                '**　総　合　計　**',
                '',
                '',
                '',
                '',
                0 if total_amount is None else "{:,}".format(total_amount),
                '',
                '',
                '',
                '',
                '',
            )
            new_data.append(last_line)
            return "\n".join(new_data)
        else:

            return new_data
