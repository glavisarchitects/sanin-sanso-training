# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import base64
import json


class AccountMove(models.Model):
    _inherit = 'account.move'

    def svf_template_export(self):

        # Prepare data sent to SVF
        customer_so_recs = self.env['sale.order'].search([('state', 'not in', ['draft', 'cancel'])])
        so_records = customer_so_recs.filtered(lambda csr: self.id in csr.invoice_ids.ids)
        if not so_records:
            raise UserError('対応する SO レコードが見つかりません。')

        customer_payment_recs = self.env['account.payment'].search(
            [('state', '=', 'posted'), ('reconciled_invoice_ids', '!=', []), ])
        payment_record = customer_payment_recs.filtered(lambda cpr: self.id in cpr.reconciled_invoice_ids.ids)
        if not payment_record:
            raise UserError('対応する Payment レコードが見つかりません。')
        # Todo: wait for account_move_line, sale_order_line data confirmation
        #             '--->                                                                                         Name Invoice,Organization,....  DATA Header (Synthetic Invoice)                                                                                                                                                                                        <---''--->                                                                                         Name Invoice,Organization,....  DATA Header (Synthetic Invoice)                                                                                                                                                                                      <---'
        data_header = '''"invoice_no","zip","address","customer_name","output_date","registration_number","name","responsible_person","organization_zip","organization_address","organization_phone","organization_fax","this_month_amount","invoice_date_due","previous_month_amount","deposit_amount","previous_month_balance","this_month_purchase","consumption_tax","date","slip_number","detail_number","product_name","quantity","unit","unit_price","price","tax_rate","summary","price_total_tax_rate10","price_total_tax_rate8","price_total_reduced_tax_rate8","price_total_no_tax","tax_amount_rate10","tax_amount_rate8","tax_amount_reduced_tax_rate8","tax_amount_no_tax","price_total","price_total_tax","payee_info"'''

        # data_file = '''"invoice_no","zip","address","customer_name","output_date","registration_number","name","responsible_person","organization_zip","organization_address","organization_phone","organization_fax","this_month_amount","invoice_date_due","previous_month_amount","deposit_amount","previous_month_balance","this_month_purchase","consumption_tax","date","slip_number","detail_number","product_name","quantity","unit","unit_price","price","tax_rate","summary","price_total_tax_rate10","price_total_tax_rate8","price_total_reduced_tax_rate8","price_total_no_tax","tax_amount_rate10","tax_amount_rate8","tax_amount_reduced_tax_rate8","tax_amount_no_tax","price_total","price_total_tax","payee_info"
        # "1234567890","〒060-0010","札幌市中央区９条西２１丁目１番地１１号","大槻食材株式会社　札幌店　様","2020年9月20日","T1234567890123","山陰酸素工業　出雲支店","支店長：山陰　太郎","〒693-0043","2020年9月20日　現在","TEL：0853-28-2866","FAX：0853-28-2870","\3,712,740","2021年10月31日","\100,000","\100,000","\0","\3,404,451","\308,289","10/31","000001","00001","振込","","","","100,000","","","1,796,645","0","1,607,806","0","179,663","0","128,624","0","3,404,451","308,289","山陰合同銀行出雲支店（当座）1002529"
        # "1234567890","〒060-0010","札幌市中央区９条西２１丁目１番地１１号","大槻食材株式会社　札幌店　様","2020年9月20日","T1234567890123","山陰酸素工業　出雲支店","支店長：山陰　太郎","〒693-0043","2020年9月20日　現在","TEL：0853-28-2866","FAX：0853-28-2870","\3,712,740","2021年10月31日","\100,000","\100,000","\0","\3,404,451","\308,289","10/31","000001","00001","現金","","","","200,000","","","1,796,645","0","1,607,806","0","179,663","0","128,624","0","3,404,451","308,289","山陰合同銀行出雲支店（当座）1002529"
        # "1234567890","〒060-0010","札幌市中央区９条西２１丁目１番地１１号","大槻食材株式会社　札幌店　様","2020年9月20日","T1234567890123","山陰酸素工業　出雲支店","支店長：山陰　太郎","〒693-0043","2020年9月20日　現在","TEL：0853-28-2866","FAX：0853-28-2870","\3,712,740","2021年10月31日","\100,000","\100,000","\0","\3,404,451","\308,289","","","","*** 入　金　計 ***","","","","300,000","","","1,796,645","0","1,607,806","0","179,663","0","128,624","0","3,404,451","308,289","山陰合同銀行出雲支店（当座）1002529"
        # "1234567890","〒060-0010","札幌市中央区９条西２１丁目１番地１１号","大槻食材株式会社　札幌店　様","2020年9月20日","T1234567890123","山陰酸素工業　出雲支店","支店長：山陰　太郎","〒693-0043","2020年9月20日　現在","TEL：0853-28-2866","FAX：0853-28-2870","\3,712,740","2021年10月31日","\100,000","\100,000","\0","\3,404,451","\308,289","10/3","000002","00002","プロパン／サプライ","9,992.10","Kg","112.80","1,127,109","課税10%","配送センター991","1,796,645","0","1,607,806","0","179,663","0","128,624","0","3,404,451","308,289","山陰合同銀行出雲支店（当座）1002529"
        # "1234567890","〒060-0010","札幌市中央区９条西２１丁目１番地１１号","大槻食材株式会社　札幌店　様","2020年9月20日","T1234567890123","山陰酸素工業　出雲支店","支店長：山陰　太郎","〒693-0043","2020年9月20日　現在","TEL：0853-28-2866","FAX：0853-28-2870","\3,712,740","2021年10月31日","\100,000","\100,000","\0","\3,404,451","\308,289","10/8","000003","00003","プロパン／サプライ","2,295.00","ｍ3","225.60","517,752","課税10%","配送センター991","1,796,645","0","1,607,806","0","179,663","0","128,624","0","3,404,451","308,289","山陰合同銀行出雲支店（当座）1002529"
        # "1234567890","〒060-0010","札幌市中央区９条西２１丁目１番地１１号","大槻食材株式会社　札幌店　様","2020年9月20日","T1234567890123","山陰酸素工業　出雲支店","支店長：山陰　太郎","〒693-0043","2020年9月20日　現在","TEL：0853-28-2866","FAX：0853-28-2870","\3,712,740","2021年10月31日","\100,000","\100,000","\0","\3,404,451","\308,289","10/10","000004","00004","プロパン／サプライ","345.60","Kg","112.80","38,984","課税10%","配送センター991","1,796,645","0","1,607,806","0","179,663","0","128,624","0","3,404,451","308,289","山陰合同銀行出雲支店（当座）1002529"
        # '''

        # 詳細（入金）Payment Data
        payment_data = ['"' + payment_record.date, payment_record.name, "", payment_record.x_receipt_type, "", "", "",
                        "{:,}".format(int(payment_record.amount)), "", "", 'x' + '"']
        r002_svf_registration_number = self.env['ir.config_parameter'].sudo().get_param(
            'invoice_report.registration_number')
        for so in so_records:
            customer_address = so.partner_invoice_id.street + '' if so.partner_invoice_id.street else ''
            customer_address += so.partner_invoice_id.street2 + '' if so.partner_invoice_id.street2 else ''
            customer_address += so.partner_invoice_id.city + '' if so.partner_invoice_id.city else ''
            customer_address += so.partner_invoice_id.state_id.name + '' if so.partner_invoice_id.state_id.name else ''
            customer_address += so.partner_invoice_id.country_id.name + '' if so.partner_invoice_id.country_id.name else ''

            organization_address = self.x_organization_id.organization_state_id.name + '' if self.x_organization_id.organization_state_id.name else ''
            organization_address += self.x_organization_id.city + '' if self.x_organization_id.city else ''
            organization_address += self.x_organization_id.street + '' if self.x_organization_id.street else ''
            organization_address += self.x_organization_id.street2 + '' if self.x_organization_id.street2 else ''

            output_date = fields.Datetime.now().strftime("%Y年%-m月%-d日")
            invoice_data = ['"' + self.name, so.partner_invoice_id.zip, customer_address,
                            so.partner_invoice_id.name + '様', output_date, r002_svf_registration_number,
                            self.x_organization_id.name, self.x_organization_id.organization_zip, organization_address,
                            self.x_organization_id.organization_fax, '下記の通りご請求申し上げます。', 'x' + '"']

        # data = {
        #     # '請求書': self.name,
        #     'invoice_no': self.partner_invoice_id.name,
        #     'registration_number': self.env['ir.config_parameter'].sudo().get_param(
        #         'invoice_report.registration_number'),
        #     'name': self.x_organization_id.name,
        #     'responsible_person': self.x_organization_id.responsible_person,
        #     'zip': so_record.partner_invoice_id.zip,
        #     'state': so_record.partner_invoice_id.state_id.name,
        #     'city': so_record.partner_invoice_id.city,
        #     'organization_zip': self.x_organization_id.organization_zip,
        #     'organization_address': self.x_organization_id.organization_state_id.name + '' + self.x_organization_id.organization_city + '' + self.x_organization_id.organization_street + '' + self.x_organization_id.organization_street2 + '',
        #     'organization_phone': self.x_organization_id.organization_phone,
        #     'organization_fax': self.x_organization_id.organization_fax,
        #     'invoice_date_due': self.invoice_date_due,
        #     'amount_total': self.amount_total,
        #     'debit': self.debit,
        #     'date_done': self.date_done,
        #     #  Payment
        #     'date': payment_record.date,
        #     'slip_number': payment_record.name,
        #     'product_name': payment_record.x_receipt_type,
        #     'price': payment_record.amount,
        #     'summary': payment_record.x_remarks,
        # }
        # self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_file, type_report='R002')

    # End Region
