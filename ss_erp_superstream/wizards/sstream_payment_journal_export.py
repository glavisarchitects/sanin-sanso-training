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

    # receipt payment p6, p7
    def query_payment_p6p7(self, param):
        start_period = datetime.combine(self.first_day_period, datetime.min.time())
        end_period = datetime.combine(self.last_day_period, datetime.max.time())

        _select_data = f"""
        WITH x_payment_type AS (
        SELECT * FROM (VALUES('bank', '振込'),
            ('transfer', '振替'),
            ('bills', '手形'),
            ('cash', '現金'),
            ('paycheck', '小切手'),
            ('branch_receipt', '他店入金'),
            ('offset', '相殺')) AS t (x_type,x_value)
        )
        select								
            am.id move_id									
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
            , case when ap.payment_type = 'inbound' and ap.partner_type = 'customer' then  '0'														
            else '2'								
            end as partner_employee_division							
            , case when ap.payment_type = 'inbound' and ap.partner_type = 'customer' then  ''														
            else rpad(right(seo.organization_code, 3), 13, '0')								
            end as partner_employee_code							
            , aml.debit :: INTEGER as journal_amount								
            , aml.debit :: INTEGER as tax_excluded_amount								
            , 0 as tax_amount								
            , '000' as tax_code								
            , '0' as tax_entry_division								
           , xpt.x_value || '／' || rp.name as apply1								
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
            --, rp.name as partner_name								
        from								
            account_move am  /* 仕訳 */	
            left join
            account_move oam 
            on oam.id = am.reversed_entry_id							
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
            on am.id = ap.move_id or (oam.id = ap.move_id AND am.reversed_entry_id is not NULL)									
            inner join								
            ss_erp_organization seo /* 組織 */								
            on am.x_organization_id = seo.id	
            left join								
            x_payment_type xpt /* 組織 */								
            on ((xpt.x_type = ap.x_receipt_type and ap.payment_type = 'inbound') OR (xpt.x_type = ap.x_payment_type and ap.payment_type = 'outbound'))								
        where								
            aml.debit <> 0								
        and am.state = 'posted'								
        and am.move_type = 'entry'								
        and am.date BETWEEN '{start_period}' and '{end_period}'								
        and (ap.x_receipt_type is not NUll and ap.payment_type = 'inbound' OR	ap.x_payment_type is not NULL and ap.payment_type = 'outbound')								
        and am.x_organization_id = '{self.branch_id.id}'
        and aml.is_super_stream_linked = False							

        UNION ALL								

        /* 貸方データ取得 */								
        select								
            am.id move_id								
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
            , case when ap.payment_type = 'inbound' and ap.partner_type = 'customer' then  '1'														
            else '0'								
            end as partner_employee_division									
            , case when ap.payment_type = 'inbound' and ap.partner_type = 'customer' then rpad(right(seo.organization_code, 3), 13, '0')														
            else ''								
            end as partner_employee_code								
            , aml.credit :: INTEGER as journal_amount								
            , aml.credit :: INTEGER as tax_excluded_amount								
            , 0 as tax_amount								
            , '000' as tax_code								
            , '0' as tax_entry_division								
            , xpt.x_value || '／' || rp.name as apply1								
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
            --, rp.name as partner_name								
        from								
            account_move am  /* 仕訳 */	
            left join
            account_move oam 
            on oam.id = am.reversed_entry_id								
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
            on am.id = ap.move_id or (oam.id = ap.move_id AND am.reversed_entry_id is not NULL)									
            inner join								
            ss_erp_organization seo /* 組織 */								
            on am.x_organization_id = seo.id
            left join								
            x_payment_type xpt /* 組織 */								
            on ((xpt.x_type = ap.x_receipt_type and ap.payment_type = 'inbound') OR (xpt.x_type = ap.x_payment_type and ap.payment_type = 'outbound'))									
        where								
            aml.credit <> 0								
        and am.state = 'posted'								
        and am.move_type = 'entry'								
        and am.date BETWEEN '{start_period}' and '{end_period}'								
        and (ap.x_receipt_type is not NUll and ap.payment_type = 'inbound' OR	ap.x_payment_type is not NULL and ap.payment_type = 'outbound')								
        and am.x_organization_id = '{self.branch_id.id}'
        and aml.is_super_stream_linked = False								
        order by 
            move_id asc	
            , deb_cre_division asc	
            , line_number asc															
            , slip_date asc								
            --, partner_name asc								
            , journal_amount asc								
            , depar_orga_code asc								
"""
        self._cr.execute(_select_data)
        data_query_payment_p6p7 = self._cr.dictfetchall()
        return data_query_payment_p6p7

    # outbound payment p6
#     def query_outbound_payment_pattern6(self, param):
#         start_period = datetime.combine(self.first_day_period, datetime.min.time())
#         end_period = datetime.combine(self.last_day_period, datetime.max.time())
#
#         _select_data = f"""
#         WITH x_payment_type AS (
#         SELECT * FROM (VALUES('bank', '振込'),
#             ('transfer', '振替'),
#             ('bills', '手形'),
#             ('cash', '現金'),
#             ('paycheck', '小切手'),
#             ('branch_receipt', '他店入金'),
#             ('offset', '相殺')) AS t (x_type,x_value)
#         )
#         select
#             ap.id payment_id
#             ,'3' as record_division
#             , '{param['sstream_company_code']}' as company_code
#             , '{param['sstream_slip_group']}' as slip_group
#             , '' as slip_number
#             , to_char(am.date, 'YYYY-MM-DD') as slip_date
#             , '1' as line_number
#             , '0' as deb_cre_division
#             , aa.code as account_code
#             , COALESCE(seas.code, '') as sub_account_code
#             , '40' || right(seo.organization_code, 3) as depar_orga_code
#             , '' as function_code1
#             , '' as function_code2
#             , '' as function_code3
#             , '' as function_code4
#             , '' as project_code1
#             , '2' as partner_employee_division
#             , rpad(right(seo.organization_code, 3), 13, '0') as partner_employee_code
#             , aml.debit :: INTEGER as journal_amount
#             , aml.debit :: INTEGER as tax_excluded_amount
#             , 0 as tax_amount
#             , '000' as tax_code
#             , '0' as tax_entry_division
#             ,  rp.name apply1
#             , '' as summary2
#             , '' as partner_ref_code
#             , '' as transaction_currency_code
#             , '' as rate_type
#             , '0' as exchange_rate
#             , 0 as transaction_currency_amount
#             , '' as spare_character_item1
#             , '' as spare_character_item2
#             , '' as spare_character_item3
#             , '' as spare_character_item4
#             , '' as spare_character_item5
#             , '' as spare_character_item6
#             , '' as spare_character_item7
#             , '' as spare_character_item8
#             , '' as reserved_numeric_item1
#             , '' as reserved_numeric_item2
#             , '' as reserved_numeric_item3
#             , rp.name as partner_name
#         from
#             account_move am  /* 仕訳 */
#             inner join
#             account_move_line aml /* 仕訳項目 */
#             on am.id = aml.move_id
#             inner join
#             account_account aa /* 勘定科目 */
#             on aml.account_id = aa.id
#             left outer join
#             ss_erp_account_subaccount seas /* 補助科目 */
#             on aml.x_sub_account_id = seas.id
#             inner join
#             ss_erp_responsible_department serd /* 管轄部門 */
#             on am.x_responsible_dept_id = serd.id
#             inner join
#             res_partner rp  /* 連絡先 */
#             on am.partner_id = rp.id
#             inner join
#             account_payment ap  /* 支払 */
#             on am.id = ap.move_id
#             inner join
#             ss_erp_organization seo /* 組織 */
#             on am.x_organization_id = seo.id
#         where
#             aml.debit <> 0
#         and am.state = 'posted'
#         and am.move_type = 'entry'
#         and am.date BETWEEN '{start_period}' and '{end_period}'
#         and ap.x_payment_type in ('bank', 'bills', 'cash')
#         and ap.payment_type = 'outbound'  /* 入金 */
#         and ap.partner_type = 'supplier'  /* 顧客 */
#         and am.x_organization_id = '{self.branch_id.id}'
#         and aml.is_super_stream_linked = False
#
#         UNION ALL
#
#         /* 貸方データ取得 */
#         select
#             ap.id payment_id
#             ,'3' as record_division
#             , '{param['sstream_company_code']}' as company_code
#             , '{param['sstream_slip_group']}' as slip_group
#             , '' as slip_number
#             , to_char(am.date, 'YYYY-MM-DD') as slip_date
#             , '4' as line_number
#             , '1' as deb_cre_division
#             , aa.code as account_code
#             , COALESCE(seas.code, '') as sub_account_code
#             , '40' || right(seo.organization_code, 3) as depar_orga_code
#             , '' as function_code1
#             , '' as function_code2
#             , '' as function_code3
#             , '' as function_code4
#             , '' as project_code1
#             , '0' as partner_employee_division
#             , '' as partner_employee_code
#             , aml.credit :: INTEGER as journal_amount
#             , aml.credit :: INTEGER as tax_excluded_amount
#             , 0 as tax_amount
#             , '000' as tax_code
#             , '0' as tax_entry_division
#             , case when ap.x_payment_type = 'bank' then  '振込' || '／' || rp.name
#             when ap.x_payment_type = 'bills' then  '手形' || '／' || rp.name
#             when ap.x_payment_type = 'cash' then  '現金' || '／' || rp.name
#             else rp.name
#             end as apply1
#             , '' as summary2
#             , '' as partner_ref_code
#             , '' as transaction_currency_code
#             , '' as rate_type
#             , '0' as exchange_rate
#             , 0 as transaction_currency_amount
#             , '' as spare_character_item1
#             , '' as spare_character_item2
#             , '' as spare_character_item3
#             , '' as spare_character_item4
#             , '' as spare_character_item5
#             , '' as spare_character_item6
#             , '' as spare_character_item7
#             , '' as spare_character_item8
#             , '' as reserved_numeric_item1
#             , '' as reserved_numeric_item2
#             , '' as reserved_numeric_item3
#             , rp.name as partner_name
#         from
#             account_move am  /* 仕訳 */
#             inner join
#             account_move_line aml /* 仕訳項目 */
#             on am.id = aml.move_id
#             inner join
#             account_account aa /* 勘定科目 */
#             on aml.account_id = aa.id
#             left outer join
#             ss_erp_account_subaccount seas /* 補助科目 */
#             on aml.x_sub_account_id = seas.id
#             inner join
#             ss_erp_responsible_department serd /* 管轄部門 */
#             on am.x_responsible_dept_id = serd.id
#             inner join
#             res_partner rp  /* 連絡先 */
#             on am.partner_id = rp.id
#             inner join
#             account_payment ap  /* 支払 */
#             on am.id = ap.move_id
#             inner join
#             ss_erp_organization seo /* 組織 */
#             on am.x_organization_id = seo.id
#         where
#             aml.credit <> 0
#         and am.state = 'posted'
#         and am.move_type = 'entry'
#         and am.date BETWEEN '{start_period}' and '{end_period}'
#         and ap.x_payment_type in ('bank', 'bills', 'cash')
#         and ap.payment_type = 'outbound'  /* 入金 */
#         and ap.partner_type = 'supplier'  /* 顧客 */
#         and am.x_organization_id = '{self.branch_id.id}'
#         and aml.is_super_stream_linked = False
#         order by
#             payment_id asc
#             , deb_cre_division asc
#             , line_number asc
#             , slip_date asc
#             , partner_name asc
#             , journal_amount asc
#             , depar_orga_code asc
# """
#         self._cr.execute(_select_data)
#         data_outbound_payment_pattern6 = self._cr.dictfetchall()
#         return data_outbound_payment_pattern6

    def payment_journal_stream_export(self):
        # Captured data start record
        file_data = "0,1" + '\r\n'

        param = self.get_a007_payment_journal_param()

        data_query_payment_p6p7 = self.query_payment_p6p7(param)
        # data_outbound_payment_p6 = self.query_outbound_payment_pattern6(self.get_a007_payment_journal_param())

        #
        all_pattern_data = data_query_payment_p6p7

        if not all_pattern_data:
            raise UserError('出力するデータが見つかりませんでした。指定した期間内に出力対象データが存在しないか、既に出力済みの可能性があります。')

        all_am_rec_id = []

        count = 0
        for index, all_data in enumerate(all_pattern_data):
            if 'move_id' in all_data:
                all_am_rec_id.append(all_data['move_id'])
                all_data.pop('move_id')
            if all_data['deb_cre_division'] == '1':
                continue
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
            journal_header = "2," + param['sstream_company_code'] + "," + param['sstream_slip_group'] + ",," + all_data[
                'slip_date'] + ',,0,1,,,,' + count_str + ',0,0,,,,,,,,,,,,,' + '\r\n'
            file_data += journal_header
            # End region

            #
            # clean_dict_data = deepcopy(all_data)
            # clean_dict_data.pop('move_id')
            # clean_dict_data.pop('partner_name')
            debit_line = ','.join(map(str, all_data.values())) + '\r\n'

            if 'move_id' in all_pattern_data[index + 1]:
                all_am_rec_id.append(all_pattern_data[index + 1]['move_id'])
                all_pattern_data[index + 1].pop('move_id')
            cre_line = all_pattern_data[index + 1]
            # clean_dict_data = deepcopy(cre_line)
            # clean_dict_data.pop('move_id')
            # clean_dict_data.pop('partner_name')
            credit_line = ','.join(map(str, cre_line.values())) + '\r\n'

            file_data += debit_line
            file_data += credit_line
            # slip data trailer record
            slip_trailer = "8" + '\r\n'
            file_data += slip_trailer

        # payment_recs = self.env['account.payment'].search([('id', 'in', all_payment_rec_id)]).mapped('move_id').ids
        journal_entry_recs = self.env['account.move'].search([('id', 'in', all_am_rec_id)])
        journal_item_recs = journal_entry_recs.line_ids
        journal_item_recs.is_super_stream_linked = True

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
