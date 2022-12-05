# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from copy import deepcopy
from datetime import datetime
import base64


def get_multi_character(n, key='0'):
    return key * n


class StreamPaymentJournalExport(models.TransientModel):
    _name = 'sstream.payment.journal.export'

    first_day_period = fields.Date(string='対象期間From')
    last_day_period = fields.Date(string='対象期間To')
    branch_id = fields.Many2one('ss_erp.organization', string='支店')

    def get_a007_payment_journal_param(self):
        sstream_company_code = self.env['ir.config_parameter'].sudo().get_param('A007_super_stream_company_code')
        if not sstream_company_code:
            raise UserError(
                'SuperStream連携用の会社コードの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_super_stream_company_code)')
        sstream_slip_group = self.env['ir.config_parameter'].sudo().get_param('A007_super_stream_slip_group')
        if not sstream_slip_group:
            raise UserError(
                'SuperStream連携用の伝票グループの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_super_stream_slip_group)')

        result = {
            'sstream_company_code': sstream_company_code,
            'sstream_slip_group': sstream_slip_group,
        }
        return result

    # receipt payment p6
    def query_receipt_payment_pattern6(self, param):
        start_period = datetime.combine(self.first_day_period, datetime.min.time())
        end_period = datetime.combine(self.last_day_period, datetime.max.time())

        _select_data = f"""
        select								
            ap.id payment_id								
            ,'3' as record_division								
            , '{param['sstream_company_code']}' as company_code								
            , '{param['sstream_slip_group']}' as slip_group								
            , '' as slip_number								
            , to_char(am.date, 'YYYY-MM-DD') as slip_date								
            , '1' as line_number								
            , '0' as deb_cre_division								
            , aa.code as account_code								
            , COALESCE(seas.code, '') as sub_account_code								
            , '40' || right(seo.organization_code, 3) as depar_orga_code								
            , '' as function_code1								
            , '' as function_code2								
            , '' as function_code3								
            , '' as function_code4								
            , '' as project_code1								
            , '0' as partner_employee_division								
            , '' as partner_employee_code							
            , aml.debit :: INTEGER as journal_amount								
            , aml.debit :: INTEGER as tax_excluded_amount								
            , 0 as tax_amount								
            , '000' as tax_code								
            , '0' as tax_entry_division								
            , case when ap.x_receipt_type = 'bank' then  '振込' || '／' || rp.name								
                   when ap.x_receipt_type = 'transfer' then  '振替' || '／' || rp.name								
                   when ap.x_receipt_type = 'bills' then  '手形' || '／' || rp.name								
                   when ap.x_receipt_type = 'cash' then  '現金' || '／' || rp.name								
                   when ap.x_receipt_type = 'paycheck' then  '小切手' || '／' || rp.name								
                   when ap.x_receipt_type = 'branch_receipt' then  '他支店入金' || '／' || rp.name								
                   when ap.x_receipt_type = 'offset' then  '相殺' || '／' || rp.name								
                   else rp.name								
              end as apply1								
            , '' as summary2								
            , '' as partner_ref_code								
            , '' as transaction_currency_code								
            , '' as rate_type								
            , '0' as exchange_rate								
            , 0 as transaction_currency_amount								
            , '' as spare_character_item1								
            , '' as spare_character_item2								
            , '' as spare_character_item3								
            , '' as spare_character_item4								
            , '' as spare_character_item5								
            , '' as spare_character_item6								
            , '' as spare_character_item7								
            , '' as spare_character_item8								
            , '' as reserved_numeric_item1								
            , '' as reserved_numeric_item2								
            , '' as reserved_numeric_item3								
            , rp.name as partner_name								
        from								
            account_move am  /* 仕訳 */								
            inner join								
            account_move_line aml /* 仕訳項目 */								
            on am.id = aml.move_id								
            inner join								
            account_account aa /* 勘定科目 */								
            on aml.account_id = aa.id								
            left outer join								
            ss_erp_account_subaccount seas /* 補助科目 */								
            on aml.x_sub_account_id = seas.id								
            inner join								
            ss_erp_responsible_department serd /* 管轄部門 */								
            on am.x_responsible_dept_id = serd.id								
            inner join								
            res_partner rp  /* 連絡先 */								
            on am.partner_id = rp.id								
            inner join								
            account_payment ap  /* 支払 */								
            on am.id = ap.move_id								
            inner join								
            ss_erp_organization seo /* 組織 */								
            on am.x_organization_id = seo.id								
        where								
            aml.debit <> 0								
        and am.state = 'posted'								
        and am.move_type = 'entry'								
        and am.date BETWEEN '{start_period}' and '{end_period}'								
        and ap.x_receipt_type in ('bank', 'transfer', 'bills', 'cash', 'paycheck', 'branch_receipt', 'offset')								
        and ap.payment_type = 'inbound'  /* 入金 */								
        and ap.partner_type = 'customer'  /* 顧客 */								
        and am.x_organization_id = '{self.branch_id.id}'
        and aml.is_super_stream_linked = False							
                                        
        UNION ALL								
                                        
        /* 貸方データ取得 */								
        select								
            ap.id payment_id							
            ,'3' as record_division							
            , '{param['sstream_company_code']}' as company_code								
            , '{param['sstream_slip_group']}' as slip_group									
            , '' as slip_number								
            , to_char(am.date, 'YYYY-MM-DD') as slip_date								
            , '4' as line_number								
            , '1' as deb_cre_division								
            , aa.code as account_code								
            , COALESCE(seas.code, '') as sub_account_code								
            , '40' || right(seo.organization_code, 3) as depar_orga_code								
            , '' as function_code1								
            , '' as function_code2								
            , '' as function_code3								
            , '' as function_code4								
            , '' as project_code1									
            , '1' as partner_employee_division								
            , rpad(right(seo.organization_code, 3), 13, '0') as partner_employee_code								
            , aml.credit :: INTEGER as journal_amount								
            , aml.credit :: INTEGER as tax_excluded_amount								
            , 0 as tax_amount								
            , '000' as tax_code								
            , '0' as tax_entry_division								
            , rp.name as apply1								
            , '' as summary2								
            , '' as partner_ref_code								
            , '' as transaction_currency_code								
            , '' as rate_type								
            , '0' as exchange_rate								
            , 0 as transaction_currency_amount								
            , '' as spare_character_item1								
            , '' as spare_character_item2								
            , '' as spare_character_item3								
            , '' as spare_character_item4								
            , '' as spare_character_item5								
            , '' as spare_character_item6								
            , '' as spare_character_item7								
            , '' as spare_character_item8								
            , '' as reserved_numeric_item1								
            , '' as reserved_numeric_item2								
            , '' as reserved_numeric_item3								
            , rp.name as partner_name								
        from								
            account_move am  /* 仕訳 */								
            inner join								
            account_move_line aml /* 仕訳項目 */								
            on am.id = aml.move_id								
            inner join								
            account_account aa /* 勘定科目 */								
            on aml.account_id = aa.id								
            left outer join								
            ss_erp_account_subaccount seas /* 補助科目 */								
            on aml.x_sub_account_id = seas.id								
            inner join								
            ss_erp_responsible_department serd /* 管轄部門 */								
            on am.x_responsible_dept_id = serd.id								
            inner join								
            res_partner rp  /* 連絡先 */								
            on am.partner_id = rp.id								
            inner join								
            account_payment ap  /* 支払 */								
            on am.id = ap.move_id								
            inner join								
            ss_erp_organization seo /* 組織 */								
            on am.x_organization_id = seo.id								
        where								
            aml.credit <> 0								
        and am.state = 'posted'								
        and am.move_type = 'entry'								
        and am.date BETWEEN '{start_period}' and '{end_period}'								
        and ap.x_receipt_type in ('bank', 'transfer', 'bills', 'cash', 'paycheck', 'branch_receipt', 'offset')								
        and ap.payment_type = 'inbound'  /* 入金 */								
        and ap.partner_type = 'customer'  /* 顧客 */								
        and am.x_organization_id = '{self.branch_id.id}'
        and aml.is_super_stream_linked = False								
        order by 								
            slip_date asc								
            , partner_name asc								
            , journal_amount asc								
            , depar_orga_code asc								
            , line_number asc								
            , deb_cre_division asc								
"""
        self._cr.execute(_select_data)
        data_receipt_payment_pattern6 = self._cr.dictfetchall()
        return data_receipt_payment_pattern6

    # outbound payment p6
    def query_outbound_payment_pattern6(self, param):
        start_period = datetime.combine(self.first_day_period, datetime.min.time())
        end_period = datetime.combine(self.last_day_period, datetime.max.time())

        _select_data = f"""
        select								
            ap.id payment_id								
            ,'3' as record_division								
            , '{param['sstream_company_code']}' as company_code								
            , '{param['sstream_slip_group']}' as slip_group								
            , '' as slip_number								
            , to_char(am.date, 'YYYY-MM-DD') as slip_date								
            , '1' as line_number								
            , '0' as deb_cre_division								
            , aa.code as account_code								
            , COALESCE(seas.code, '') as sub_account_code								
            , '40' || right(seo.organization_code, 3) as depar_orga_code								
            , '' as function_code1								
            , '' as function_code2								
            , '' as function_code3								
            , '' as function_code4								
            , '' as project_code1								
            , '2' as partner_employee_division								
            , rpad(right(seo.organization_code, 3), 13, '0') as partner_employee_code							
            , aml.debit :: INTEGER as journal_amount								
            , aml.debit :: INTEGER as tax_excluded_amount								
            , 0 as tax_amount								
            , '000' as tax_code								
            , '0' as tax_entry_division								
            ,  rp.name apply1								
            , '' as summary2								
            , '' as partner_ref_code								
            , '' as transaction_currency_code								
            , '' as rate_type								
            , '0' as exchange_rate								
            , 0 as transaction_currency_amount								
            , '' as spare_character_item1								
            , '' as spare_character_item2								
            , '' as spare_character_item3								
            , '' as spare_character_item4								
            , '' as spare_character_item5								
            , '' as spare_character_item6								
            , '' as spare_character_item7								
            , '' as spare_character_item8								
            , '' as reserved_numeric_item1								
            , '' as reserved_numeric_item2								
            , '' as reserved_numeric_item3								
            , rp.name as partner_name								
        from								
            account_move am  /* 仕訳 */								
            inner join								
            account_move_line aml /* 仕訳項目 */								
            on am.id = aml.move_id								
            inner join								
            account_account aa /* 勘定科目 */								
            on aml.account_id = aa.id								
            left outer join								
            ss_erp_account_subaccount seas /* 補助科目 */								
            on aml.x_sub_account_id = seas.id								
            inner join								
            ss_erp_responsible_department serd /* 管轄部門 */								
            on am.x_responsible_dept_id = serd.id								
            inner join								
            res_partner rp  /* 連絡先 */								
            on am.partner_id = rp.id								
            inner join								
            account_payment ap  /* 支払 */								
            on am.id = ap.move_id								
            inner join								
            ss_erp_organization seo /* 組織 */								
            on am.x_organization_id = seo.id								
        where								
            aml.debit <> 0								
        and am.state = 'posted'								
        and am.move_type = 'entry'								
        and am.date BETWEEN '{start_period}' and '{end_period}'								
        and ap.x_payment_type in ('bank', 'bills', 'cash')							
        and ap.payment_type = 'outbound'  /* 入金 */								
        and ap.partner_type = 'supplier'  /* 顧客 */								
        and am.x_organization_id = '{self.branch_id.id}'
        and aml.is_super_stream_linked = False							
                                        
        UNION ALL								
                                        
        /* 貸方データ取得 */								
        select								
            ap.id payment_id							
            ,'3' as record_division							
            , '{param['sstream_company_code']}' as company_code								
            , '{param['sstream_slip_group']}' as slip_group									
            , '' as slip_number								
            , to_char(am.date, 'YYYY-MM-DD') as slip_date								
            , '4' as line_number								
            , '1' as deb_cre_division								
            , aa.code as account_code								
            , COALESCE(seas.code, '') as sub_account_code								
            , '40' || right(seo.organization_code, 3) as depar_orga_code								
            , '' as function_code1								
            , '' as function_code2								
            , '' as function_code3								
            , '' as function_code4								
            , '' as project_code1									
            , '0' as partner_employee_division								
            , '' as partner_employee_code								
            , aml.credit :: INTEGER as journal_amount								
            , aml.credit :: INTEGER as tax_excluded_amount								
            , 0 as tax_amount								
            , '000' as tax_code								
            , '0' as tax_entry_division								
            , case when ap.x_payment_type = 'bank' then  '振込' || '／' || rp.name							
            when ap.x_payment_type = 'bills' then  '手形' || '／' || rp.name							
            when ap.x_payment_type = 'cash' then  '現金' || '／' || rp.name							
            else rp.name							
            end as apply1								
            , '' as summary2								
            , '' as partner_ref_code								
            , '' as transaction_currency_code								
            , '' as rate_type								
            , '0' as exchange_rate								
            , 0 as transaction_currency_amount								
            , '' as spare_character_item1								
            , '' as spare_character_item2								
            , '' as spare_character_item3								
            , '' as spare_character_item4								
            , '' as spare_character_item5								
            , '' as spare_character_item6								
            , '' as spare_character_item7								
            , '' as spare_character_item8								
            , '' as reserved_numeric_item1								
            , '' as reserved_numeric_item2								
            , '' as reserved_numeric_item3								
            , rp.name as partner_name								
        from								
            account_move am  /* 仕訳 */								
            inner join								
            account_move_line aml /* 仕訳項目 */								
            on am.id = aml.move_id								
            inner join								
            account_account aa /* 勘定科目 */								
            on aml.account_id = aa.id								
            left outer join								
            ss_erp_account_subaccount seas /* 補助科目 */								
            on aml.x_sub_account_id = seas.id								
            inner join								
            ss_erp_responsible_department serd /* 管轄部門 */								
            on am.x_responsible_dept_id = serd.id								
            inner join								
            res_partner rp  /* 連絡先 */								
            on am.partner_id = rp.id								
            inner join								
            account_payment ap  /* 支払 */								
            on am.id = ap.move_id								
            inner join								
            ss_erp_organization seo /* 組織 */								
            on am.x_organization_id = seo.id								
        where								
            aml.credit <> 0								
        and am.state = 'posted'								
        and am.move_type = 'entry'								
        and am.date BETWEEN '{start_period}' and '{end_period}'								
        and ap.x_payment_type in ('bank', 'bills', 'cash')							
        and ap.payment_type = 'outbound'  /* 入金 */								
        and ap.partner_type = 'supplier'  /* 顧客 */								
        and am.x_organization_id = '{self.branch_id.id}'
        and aml.is_super_stream_linked = False								
        order by 								
            slip_date asc								
            , partner_name asc								
            , journal_amount asc								
            , depar_orga_code asc								
            , line_number asc								
            , deb_cre_division asc								
"""
        self._cr.execute(_select_data)
        data_outbound_payment_pattern6 = self._cr.dictfetchall()
        return data_outbound_payment_pattern6

    def payment_journal_stream_export(self):
        # Captured data start record
        file_data = "0,1" + '\r\n'

        param = self.get_a007_payment_journal_param()

        data_receipt_payment_p6 = self.query_receipt_payment_pattern6(self.get_a007_payment_journal_param())
        data_outbound_payment_p6 = self.query_outbound_payment_pattern6(self.get_a007_payment_journal_param())

        #
        all_pattern_data = data_receipt_payment_p6 + data_outbound_payment_p6

        if not all_pattern_data:
            raise UserError('出力するデータが見つかりませんでした。指定した期間内に出力対象データが存在しないか、既に出力済みの可能性があります。')

        for all_data in all_pattern_data:
            payment_rec = self.env['account.payment'].search([('id', '=', all_data['payment_id'])])
            journal_entry_rec = payment_rec.move_id
            journal_item_recs = journal_entry_rec.line_ids
            journal_item_recs.is_super_stream_linked = True
        debit_line_data = []
        credit_line_data = []
        for all_data in all_pattern_data:
            if all_data['deb_cre_division'] == '0':
                debit_line_data.append(all_data)
            else:
                credit_line_data.append(all_data)

        count = 0
        for de_line in debit_line_data:
            # Document data header record
            doc_header = "1" + '\r\n'
            file_data += doc_header

            # other_system_slip_number_int = 1
            # other_system_slip_number_str = str(other_system_slip_number_int)
            # other_system_slip_number = get_multi_character(
            #     7 - len(other_system_slip_number_str)) + other_system_slip_number_str
            # other_system_slip_number_int += 1

            count+=1
            count_str = str(count).zfill(7)
            #     # journal entry header region
            journal_header = "2," + param['sstream_company_code'] + "," + param['sstream_slip_group'] + ",," + de_line[
                'slip_date'] + ',,0,1,,,,' + count_str + ',0,0,,,,,,,,,,,,,' + '\r\n'
            file_data += journal_header
            # End region

            debit_line = ''
            credit_line = ''

            #
            clean_dict_data = deepcopy(de_line)
            clean_dict_data.pop('payment_id')
            clean_dict_data.pop('partner_name')
            debit_line = ','.join(map(str, clean_dict_data.values())) + '\r\n'

            for cre_line in credit_line_data:
                if cre_line['payment_id'] == de_line['payment_id']:
                    clean_dict_data = deepcopy(cre_line)
                    clean_dict_data.pop('payment_id')
                    clean_dict_data.pop('partner_name')
                    credit_line = ','.join(map(str, clean_dict_data.values())) + '\r\n'
                    continue

            file_data += debit_line
            file_data += credit_line
            # slip data trailer record
            slip_trailer = "8" + '\r\n'
            file_data += slip_trailer
        # end data trailer record
        end_trailer = "9" + '\r\n'
        file_data += end_trailer
        # end record
        b = file_data.encode('shift-jis')
        file_name = 'KEIRI_' + self.branch_id.organization_code + '.txt'
        vals = {
            'name': file_name,
            'datas': base64.b64encode(b).decode('shift-jis'),
            'type': 'binary',
            'res_model': 'ir.ui.view',
            'res_id': False,
            'x_no_need_save': True,
        }

        file_txt = self.env['ir.attachment'].create(vals)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_txt.id) + '?download=true',
            'target': 'new',
        }
