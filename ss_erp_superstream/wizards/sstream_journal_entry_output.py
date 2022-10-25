# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round, float_is_zero
from datetime import datetime
import base64
import calendar


class SStreamJournalEntryOutput(models.TransientModel):
    _name = 'sstream.journal.entry.output'

    first_day_period = fields.Date(string='First Day')
    last_day_period = fields.Date(string='Last Day')

    def get_a007_param(self):
        sstream_company_code = self.env['ir.config_parameter'].sudo().get_param('A007_super_stream_company_code')
        if not sstream_company_code:
            raise UserError('SuperStream連携用の会社コードの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')
        sstream_slip_group = self.env['ir.config_parameter'].sudo().get_param('A007_super_stream_slip_group')
        if not sstream_slip_group:
            raise UserError('SuperStream連携用の伝票グループの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        sstream_linkage_recs = self.env['ss_erp.superstream.linkage.journal'].search(
            [('journal_creation', '=', 'odoo_journal')])
        if not sstream_linkage_recs:
            raise UserError('一致するリンケージ ジャーナルが見つかりませんでした。')

        result = {
            'sstream_company_code': sstream_company_code,
            'sstream_slip_group': sstream_slip_group,
            'sstream_linkage_recs': sstream_linkage_recs,
        }
        return result

    # with debit - no credit
    def query_pattern1(self, param):
        debit_accounts = param['sstream_linkage_recs'].mapped('debit_account')
        # credit_accounts = param['sstream_linkage_recs'].mapped('credit_account')
        debit_account_ids = f"({','.join(map(str, debit_accounts.ids))})"
        # credit_account_ids = f"({','.join(map(str, credit_accounts.ids))})"
        start_period = datetime.combine(self.first_day_period, datetime.min.time())
        end_period = datetime.combine(self.last_day_period, datetime.max.time())

        _select_data = f""" 
            select								
                move_line_id								
                , account_id								
                , organization_code								
                , department_code								
                , record_division								
                , company_code								
                , slip_group								
                , journal_item_label								
                , slip_date								
                , line_number								
                , deb_cre_division								
                , account_code								
                , sub_account_code								
                , depar_orga_code								
                , partner_employee_division								
                , partner_employee_code								
                , journal_amount								
                , tax_excluded_amount								
                , tax_amount								
                , case when deb_cre_division = '1' then '0'								
                       else tax_id								
                  end as tax_id								
                , tax_entry_division								
                , product								
            from(								
                select
                    move_line_id								
                    ,account_id								
                    ,organization_code								
                    , department_code								
                    , record_division								
                    , company_code								
                    , slip_group								
                    , journal_item_label								
                    , slip_date								
                    , line_number								
                    , deb_cre_division								
                    , account_code								
                    , sub_account_code								
                    , depar_orga_code								
                    , partner_employee_division								
                    , partner_employee_code								
                    , journal_amount								
                    , tax_excluded_amount								
                    , tax_amount								
                    , tax_id								
                    , tax_entry_division								
                    , product								
                from 								
                (								
                    /* 消費税のある入庫請求仮とその消費税を取得する（借方-税計算なし） */								
                    select
                         aml.id as move_line_id   
                        ,aml.account_id as account_id   
                        ,'3' as record_division								
                        , '{param['sstream_company_code']}' as company_code								
                        , '{param['sstream_slip_group']}' as slip_group	
                        , aml.name as journal_item_label							
                        , to_char(date_trunc('month', am.date) + '1 month' + '-1 Day', 'YYYY/MM/DD') as slip_date								
                        , '1' as line_number 								
                        , '0' as deb_cre_division								
                        , aa.code as account_code								
                        , COALESCE(seas.code, '') as sub_account_code								
                        , serd.code || right(seo.organization_code, 3) as depar_orga_code								
                        , '0' as partner_employee_division								
                        , '' as partner_employee_code								
                        , seo.organization_code as organization_code								
                        , serd.code as department_code								
                        , aml.price_total as journal_amount								
                        , aml.debit as tax_excluded_amount								
                        , aml.price_total - aml.debit as tax_amount								
                        , aml_atr.account_tax_id as tax_id								
                        , '2' as tax_entry_division								
                        , pt.name as product								
                    from								
                        account_move am /* 仕訳 */								
                        inner join								
                        account_move_line aml /* 仕訳項目 */								
                        on am.id = aml.move_id								
                        inner join								
                        account_move_line_account_tax_rel aml_atr /* account_move_line_account_tax_rel */								
                        on aml.id = aml_atr.account_move_line_id								
                        inner join 								
                        ss_erp_organization seo  /* 組織 */								
                        on am.x_organization_id = seo.id								
                        inner join								
                        ss_erp_responsible_department serd /* 管轄部門 */								
                        on am.x_responsible_dept_id = serd.id								
                        inner join								
                        account_account aa /* 勘定科目 */								
                        on aml.account_id = aa.id								
                        left outer join								
                        ss_erp_account_subaccount seas /* 補助科目 */								
                        on aml.x_sub_account_id = seas.id								
                        inner join								
                        product_template pt  /* プロダクトテンプレート */								
                        on aml.product_id = pt.id								
                    where								
                    aml.account_id IN {debit_account_ids} /* 貸方勘定科目を条件にする */								
                    and aml.debit <> 0  /* 借方を取得 */								
                    and parent_state = 'posted'  /* 記帳済み */								
                    and is_super_stream_linked = False  /* SuperStream未連携 */								
                    and am.date BETWEEN '{start_period}' and '{end_period}'														
                                            
                union all								
                                                
                /* 消費税のある商品売上とその消費税を取得する（貸方-税計算あり） */								
                select 								
                    aml.id as move_line_id
                    ,aml.account_id as account_id 								
                    ,'3' as record_division								
                    , '{param['sstream_company_code']}' as company_code								
                    , '{param['sstream_slip_group']}' as slip_group								
                    , aml.name as journal_item_label								
                    , to_char(date_trunc('month', am.date) + '1 month' + '-1 Day', 'YYYY/MM/DD') as slip_date								
                    , '2' as line_number 								
                    , '1' as deb_cre_division								
                    , aa.code as account_code								
                    , COALESCE(seas.code, '') as sub_account_code								
                    , serd.code || right(seo.organization_code, 3) as depar_orga_code								
                    , '2' as partner_employee_division								
                    , rpad(right(seo.organization_code, 3), 13, '0') as partner_employee_code							
                    , seo.organization_code as organization_code								
                    , serd.code as department_code								
                    , aml.price_total as journal_amount								
                    , aml.credit as tax_excluded_amount								
                    , 0 as tax_amount								
                    , '000' as tax_id								
                    , '0' as tax_entry_division								
                    , pt.name as product								
                from								
                    account_move am /* 仕訳 */								
                    inner join								
                    account_move_line aml /* 仕訳項目 */								
                    on am.id = aml.move_id								
                    inner join								
                    account_move_line_account_tax_rel aml_atr /* account_move_line_account_tax_rel */								
                    on aml.id = aml_atr.account_move_line_id								
                    inner join 								
                    ss_erp_organization seo  /* 組織 */								
                    on am.x_organization_id = seo.id								
                    inner join								
                    ss_erp_responsible_department serd /* 管轄部門 */								
                    on am.x_responsible_dept_id = serd.id								
                    inner join								
                    account_account aa /* 勘定科目 */								
                    on aml.account_id = aa.id								
                    left outer join								
                    ss_erp_account_subaccount seas /* 補助科目 */								
                    on aml.x_sub_account_id = seas.id								
                    inner join								
                    product_template pt  /* プロダクトテンプレート */								
                    on aml.product_id = pt.id								
                where								
                aml.account_id IN {debit_account_ids} /* 貸方勘定科目を条件にする */								
                and aml.debit <> 0  /* 借方を取得 */								
                and parent_state = 'posted'  /* 記帳済み */								
                and is_super_stream_linked = False  /* SuperStream未連携 */								
                and am.date BETWEEN '{start_period}' and '{end_period}'																
                ) result								
                order by								
                   product asc								
                    , organization_code asc								
                    , department_code asc								
                    , tax_id asc  								
                    , deb_cre_division asc								
                    , line_number asc  								
            )result2								

        """
        self._cr.execute(_select_data)
        data_pattern1 = self._cr.dictfetchall()
        return data_pattern1

    # no debit - with credit
    def query_pattern2(self, param):
        credit_accounts = param['sstream_linkage_recs'].mapped('credit_account')
        credit_account_ids = f"({','.join(map(str, credit_accounts.ids))})"
        start_period = datetime.combine(self.first_day_period, datetime.min.time())
        end_period = datetime.combine(self.last_day_period, datetime.max.time())

        _select_data = f""" 
            select								
                move_line_id								
                , account_id								
                , organization_code								
                , department_code								
                , record_division								
                , company_code								
                , slip_group								
                , journal_item_label								
                , slip_date								
                , line_number								
                , deb_cre_division								
                , account_code								
                , sub_account_code								
                , depar_orga_code								
                , partner_employee_division								
                , partner_employee_code								
                , journal_amount								
                , tax_excluded_amount								
                , tax_amount								
                , case when deb_cre_division = '1' then '0'								
                       else tax_id								
                  end as tax_id								
                , tax_entry_division								
                , product								
            from(								
                select
                    move_line_id								
                    ,account_id								
                    ,organization_code								
                    , department_code								
                    , record_division								
                    , company_code								
                    , slip_group								
                    , journal_item_label								
                    , slip_date								
                    , line_number								
                    , deb_cre_division								
                    , account_code								
                    , sub_account_code								
                    , depar_orga_code								
                    , partner_employee_division								
                    , partner_employee_code								
                    , journal_amount								
                    , tax_excluded_amount								
                    , tax_amount								
                    , tax_id								
                    , tax_entry_division								
                    , product								
                from 								
                (								
                    /* 消費税のある入庫請求仮とその消費税を取得する（借方-税計算なし） */								
                    select
                         aml.id as move_line_id   
                        ,aml.account_id as account_id   
                        ,'3' as record_division								
                        , '{param['sstream_company_code']}' as company_code								
                        , '{param['sstream_slip_group']}' as slip_group	
                        , aml.name as journal_item_label							
                        , to_char(date_trunc('month', am.date) + '1 month' + '-1 Day', 'YYYY/MM/DD') as slip_date								
                        , '1' as line_number 								
                        , '0' as deb_cre_division								
                        , aa.code as account_code								
                        , COALESCE(seas.code, '') as sub_account_code								
                        , serd.code || right(seo.organization_code, 3) as depar_orga_code								
                        , '0' as partner_employee_division								
                        , '' as partner_employee_code								
                        , seo.organization_code as organization_code								
                        , serd.code as department_code								
                        , aml.price_total as journal_amount								
                        , aml.price_total as tax_excluded_amount								
                        , 0 as tax_amount								
                        , aml_atr.account_tax_id as tax_id								
                        , '2' as tax_entry_division								
                        , pt.name as product								
                    from								
                        account_move am /* 仕訳 */								
                        inner join								
                        account_move_line aml /* 仕訳項目 */								
                        on am.id = aml.move_id								
                        inner join								
                        account_move_line_account_tax_rel aml_atr /* account_move_line_account_tax_rel */								
                        on aml.id = aml_atr.account_move_line_id								
                        inner join 								
                        ss_erp_organization seo  /* 組織 */								
                        on am.x_organization_id = seo.id								
                        inner join								
                        ss_erp_responsible_department serd /* 管轄部門 */								
                        on am.x_responsible_dept_id = serd.id								
                        inner join								
                        account_account aa /* 勘定科目 */								
                        on aml.account_id = aa.id								
                        left outer join								
                        ss_erp_account_subaccount seas /* 補助科目 */								
                        on aml.x_sub_account_id = seas.id								
                        inner join								
                        product_template pt  /* プロダクトテンプレート */								
                        on aml.product_id = pt.id								
                    where								
                    aml.account_id IN {credit_account_ids} /* 貸方勘定科目を条件にする */								
                    and aml.credit <> 0  /* 借方を取得 */								
                    and parent_state = 'posted'  /* 記帳済み */								
                    and is_super_stream_linked = False  /* SuperStream未連携 */								
                    and am.date BETWEEN '{start_period}' and '{end_period}'														
                                            
                union all								
                                                
                /* 消費税のある商品売上とその消費税を取得する（貸方-税計算あり） */								
                select 								
                    aml.id as move_line_id
                    ,aml.account_id as account_id 								
                    ,'3' as record_division								
                    , '{param['sstream_company_code']}' as company_code								
                    , '{param['sstream_slip_group']}' as slip_group								
                    , aml.name as journal_item_label								
                    , to_char(date_trunc('month', am.date) + '1 month' + '-1 Day', 'YYYY/MM/DD') as slip_date								
                    , '2' as line_number 								
                    , '1' as deb_cre_division								
                    , aa.code as account_code								
                    , COALESCE(seas.code, '') as sub_account_code								
                    , serd.code || right(seo.organization_code, 3) as depar_orga_code								
                    , '2' as partner_employee_division								
                    , rpad(right(seo.organization_code, 3), 13, '0') as partner_employee_code							
                    , seo.organization_code as organization_code								
                    , serd.code as department_code								
                    , aml.price_total as journal_amount								
                    , aml.credit as tax_excluded_amount								
                    , aml.price_total as tax_amount								
                    , '000' as tax_id								
                    , '0' as tax_entry_division								
                    , pt.name as product								
                from								
                    account_move am /* 仕訳 */								
                    inner join								
                    account_move_line aml /* 仕訳項目 */								
                    on am.id = aml.move_id								
                    inner join								
                    account_move_line_account_tax_rel aml_atr /* account_move_line_account_tax_rel */								
                    on aml.id = aml_atr.account_move_line_id								
                    inner join 								
                    ss_erp_organization seo  /* 組織 */								
                    on am.x_organization_id = seo.id								
                    inner join								
                    ss_erp_responsible_department serd /* 管轄部門 */								
                    on am.x_responsible_dept_id = serd.id								
                    inner join								
                    account_account aa /* 勘定科目 */								
                    on aml.account_id = aa.id								
                    left outer join								
                    ss_erp_account_subaccount seas /* 補助科目 */								
                    on aml.x_sub_account_id = seas.id								
                    inner join								
                    product_template pt  /* プロダクトテンプレート */								
                    on aml.product_id = pt.id								
                where								
                aml.account_id IN {credit_account_ids} /* 貸方勘定科目を条件にする */								
                and aml.credit <> 0  /* 借方を取得 */								
                and parent_state = 'posted'  /* 記帳済み */								
                and is_super_stream_linked = False  /* SuperStream未連携 */								
                and am.date BETWEEN '{start_period}' and '{end_period}'																
                ) result								
                order by								
                   product asc								
                    , organization_code asc								
                    , department_code asc								
                    , tax_id asc  								
                    , deb_cre_division asc								
                    , line_number asc  								
            )pattern2								

        """
        self._cr.execute(_select_data)
        data_pattern2 = self._cr.dictfetchall()
        return data_pattern2

    # no debit - no credit
    def query_pattern3(self, param):
        credit_accounts = param['sstream_linkage_recs'].mapped('credit_account')
        credit_account_ids = f"({','.join(map(str, credit_accounts.ids))})"

        debit_accounts = param['sstream_linkage_recs'].mapped('debit_account')
        debit_account_ids = f"({','.join(map(str, debit_accounts.ids))})"

        start_period = datetime.combine(self.first_day_period, datetime.min.time())
        end_period = datetime.combine(self.last_day_period, datetime.max.time())

        _select_data = f""" 
            select								
                move_line_id								
                , account_id								
                , organization_code								
                , department_code								
                , record_division								
                , company_code								
                , slip_group								
                , journal_item_label								
                , slip_date								
                , line_number								
                , deb_cre_division								
                , account_code								
                , sub_account_code								
                , depar_orga_code								
                , partner_employee_division								
                , partner_employee_code								
                , journal_amount								
                , tax_excluded_amount								
                , tax_amount								
                , case when deb_cre_division = '1' then '0'								
                       else tax_id								
                  end as tax_id								
                , tax_entry_division								
                , product								
            from(								
                select
                    move_line_id								
                    ,account_id								
                    ,organization_code								
                    , department_code								
                    , record_division								
                    , company_code								
                    , slip_group								
                    , journal_item_label								
                    , slip_date								
                    , line_number								
                    , deb_cre_division								
                    , account_code								
                    , sub_account_code								
                    , depar_orga_code								
                    , partner_employee_division								
                    , partner_employee_code								
                    , journal_amount								
                    , tax_excluded_amount								
                    , tax_amount								
                    , tax_id								
                    , tax_entry_division								
                    , product								
                from 								
                (								
                    /* 消費税のある入庫請求仮とその消費税を取得する（借方-税計算なし） */								
                    select
                         aml.id as move_line_id   
                        ,aml.account_id as account_id   
                        ,'3' as record_division								
                        , '{param['sstream_company_code']}' as company_code								
                        , '{param['sstream_slip_group']}' as slip_group	
                        , aml.name as journal_item_label							
                        , to_char(date_trunc('month', am.date) + '1 month' + '-1 Day', 'YYYY/MM/DD') as slip_date								
                        , '1' as line_number 								
                        , '0' as deb_cre_division								
                        , aa.code as account_code								
                        , COALESCE(seas.code, '') as sub_account_code								
                        , serd.code || right(seo.organization_code, 3) as depar_orga_code								
                        , '0' as partner_employee_division								
                        , '' as partner_employee_code								
                        , seo.organization_code as organization_code								
                        , serd.code as department_code								
                        , aml.debit as journal_amount								
                        , aml.debit as tax_excluded_amount								
                        , 0 as tax_amount								
                        , aml_atr.account_tax_id as tax_id								
                        , '2' as tax_entry_division								
                        , pt.name as product								
                    from								
                        account_move am /* 仕訳 */								
                        inner join								
                        account_move_line aml /* 仕訳項目 */								
                        on am.id = aml.move_id								
                        inner join								
                        account_move_line_account_tax_rel aml_atr /* account_move_line_account_tax_rel */								
                        on aml.id = aml_atr.account_move_line_id								
                        inner join 								
                        ss_erp_organization seo  /* 組織 */								
                        on am.x_organization_id = seo.id								
                        inner join								
                        ss_erp_responsible_department serd /* 管轄部門 */								
                        on am.x_responsible_dept_id = serd.id								
                        inner join								
                        account_account aa /* 勘定科目 */								
                        on aml.account_id = aa.id								
                        left outer join								
                        ss_erp_account_subaccount seas /* 補助科目 */								
                        on aml.x_sub_account_id = seas.id								
                        inner join								
                        product_template pt  /* プロダクトテンプレート */								
                        on aml.product_id = pt.id								
                    where								
                    aml.account_id IN {debit_account_ids} /* 貸方勘定科目を条件にする */								
                    and aml.credit <> 0  /* 借方を取得 */								
                    and parent_state = 'posted'  /* 記帳済み */								
                    and is_super_stream_linked = False  /* SuperStream未連携 */								
                    and am.date BETWEEN '{start_period}' and '{end_period}'														
                                            
                union all								
                                                
                /* 消費税のある商品売上とその消費税を取得する（貸方-税計算あり） */								
                select 								
                    aml.id as move_line_id
                    ,aml.account_id as account_id 								
                    ,'3' as record_division								
                    , '{param['sstream_company_code']}' as company_code								
                    , '{param['sstream_slip_group']}' as slip_group								
                    , aml.name as journal_item_label								
                    , to_char(date_trunc('month', am.date) + '1 month' + '-1 Day', 'YYYY/MM/DD') as slip_date								
                    , '2' as line_number 								
                    , '1' as deb_cre_division								
                    , aa.code as account_code								
                    , COALESCE(seas.code, '') as sub_account_code								
                    , serd.code || right(seo.organization_code, 3) as depar_orga_code								
                    , '2' as partner_employee_division								
                    , rpad(right(seo.organization_code, 3), 13, '0') as partner_employee_code							
                    , seo.organization_code as organization_code								
                    , serd.code as department_code								
                    , aml.credit as journal_amount								
                    , aml.credit as tax_excluded_amount								
                    , 0 as tax_amount								
                    , '000' as tax_id								
                    , '0' as tax_entry_division								
                    , pt.name as product								
                from								
                    account_move am /* 仕訳 */								
                    inner join								
                    account_move_line aml /* 仕訳項目 */								
                    on am.id = aml.move_id								
                    inner join								
                    account_move_line_account_tax_rel aml_atr /* account_move_line_account_tax_rel */								
                    on aml.id = aml_atr.account_move_line_id								
                    inner join 								
                    ss_erp_organization seo  /* 組織 */								
                    on am.x_organization_id = seo.id								
                    inner join								
                    ss_erp_responsible_department serd /* 管轄部門 */								
                    on am.x_responsible_dept_id = serd.id								
                    inner join								
                    account_account aa /* 勘定科目 */								
                    on aml.account_id = aa.id								
                    left outer join								
                    ss_erp_account_subaccount seas /* 補助科目 */								
                    on aml.x_sub_account_id = seas.id								
                    inner join								
                    product_template pt  /* プロダクトテンプレート */								
                    on aml.product_id = pt.id								
                where								
                aml.account_id IN {credit_account_ids} /* 貸方勘定科目を条件にする */								
                and aml.credit <> 0  /* 借方を取得 */								
                and parent_state = 'posted'  /* 記帳済み */								
                and is_super_stream_linked = False  /* SuperStream未連携 */								
                and am.date BETWEEN '{start_period}' and '{end_period}'																
                ) result								
                order by								
                   product asc								
                    , organization_code asc								
                    , department_code asc								
                    , tax_id asc  								
                    , deb_cre_division asc								
                    , line_number asc  								
            )pattern3								

        """
        self._cr.execute(_select_data)
        data_pattern3 = self._cr.dictfetchall()
        return data_pattern3

    def concatenate_summary(self, linkage_journal_rec, line_data):
        summary1 = ''
        if linkage_journal_rec.credit_application_edit_indicator == 'month':
            summary1 = line_data['journal_item_label'] + " " + line_data['slip_date'][5:6] + "月分"
        elif linkage_journal_rec.credit_application_edit_indicator == 'month_and_branch':
            organization = self.env['ss_erp.organization'].search(
                [('organization_code', '=', line_data['organization_code'])], limit=1)

            summary1 = line_data['journal_item_label'] + " " + line_data['slip_date'][5:6] + "月分" + "/" + organization.name
        return summary1

    def export_sstream_journal_entry(self):
        # Captured data start record
        file_data = "0,1" + '\r\n'

        param = self.get_a007_param()


        pattern1_data = self.query_pattern1(self.get_a007_param())
        for p1d in pattern1_data: p1d['pattern_type'] = 1
        pattern2_data = self.query_pattern2(self.get_a007_param())
        for p2d in pattern2_data: p2d['pattern_type'] = 2
        pattern3_data = self.query_pattern3(self.get_a007_param())
        for p3d in pattern3_data: p3d['pattern_type'] = 3

        all_pattern_data = pattern1_data + pattern2_data
        debit_line_data = []
        credit_line_data = []
        for p1d in all_pattern_data:
            if p1d['deb_cre_division'] == '0':
                debit_line_data.append(p1d)
            else:
                credit_line_data.append(p1d)

        for de_line in debit_line_data:
            # Document data header record
            doc_header = "1" + '\r\n'
            file_data += doc_header

            # journal entry header region
            journal_header = "2," + param['sstream_company_code'] + "," + param['sstream_slip_group'] + ",," + de_line[
                'slip_date'] + ',,0,1,,,,,0,0,,,,,,,,,,,,,' + '\r\n'
            file_data += journal_header
            # End region
            # pattern 1
            if de_line['pattern_type'] == 1:
                linkage_journal_rec = param['sstream_linkage_recs'].filtered(lambda r: r.debit_account.id == int(de_line['account_id']))
            # pattern 2
            elif de_line['pattern_type'] == 2:
                linkage_journal_rec = param['sstream_linkage_recs'].filtered(lambda r: r.credit_account.id == int(de_line['account_id']))
            # pattern 3
            elif de_line['pattern_type'] == 3:
                linkage_journal_rec = param['sstream_linkage_recs'].filtered(lambda r: r.debit_account.id == int(de_line['account_id']))

            if len(linkage_journal_rec) != 1:
                raise UserError(_('linkage.journal が見つからないか、一致するレコードが複数あります'))

            summary1 = self.concatenate_summary(linkage_journal_rec, de_line)

            #     # end region
            debit_line = ''
            credit_line = ''
            # tax region
            account_tax = self.env['account.tax'].browse(de_line['tax_id'])

            convert_tax_code_type = self.env['ss_erp.convert.code.type'].search([('code', '=', 'tax_code')],
                                                                                limit=1)
            external_system_type = self.env['ss_erp.external.system.type'].search(
                [('code', '=', 'super_stream')],
                limit=1)
            convert_tax_recs = self.env['ss_erp.code.convert'].search(
                [('convert_code_type', '=', convert_tax_code_type.id),
                 ('external_system', '=', external_system_type.id)], )
            convert_tax_map = convert_tax_recs.filtered(lambda r: r.internal_code.id == account_tax.id)

            external_tax_code = convert_tax_map.external_code or ''

            debit_line = de_line['record_division'] + ',' + de_line['company_code'] + ',' + de_line['slip_group'] + ',,' + \
                         de_line[
                             'slip_date'] + ',' + de_line['line_number'] + ',' + de_line['deb_cre_division'] + ',' + de_line[
                             'account_code'] + ',' + de_line['sub_account_code'] + ',' + de_line[
                             'depar_orga_code'] + ',,,,,,' + de_line['partner_employee_division'] + ',' + de_line[
                             'partner_employee_code'] + ',' + str(de_line['journal_amount']) + ',' + \
                         str(de_line['tax_excluded_amount']) + ',' + str(
                de_line['tax_amount']) + ',' + external_tax_code + ',' + \
                         de_line['tax_entry_division'] + ',' + summary1 + ',,,,,0,0,,,,,,,,,,,' + '\r\n'
            for cre_line in credit_line_data:
                if cre_line['pattern_type'] == 3:
                    linkage_journal_rec = param['sstream_linkage_recs'].filtered(lambda r: r.credit_account.id == int(cre_line['account_id']))
                    summary1 = self.concatenate_summary(linkage_journal_rec, cre_line)
                if cre_line['move_line_id'] == de_line['move_line_id']:
                    credit_line = cre_line['record_division'] + ',' + cre_line['company_code'] + ',' + cre_line[
                        'slip_group'] + ',,' + cre_line[
                                      'slip_date'] + ',' + cre_line['line_number'] + ',' + cre_line[
                                      'deb_cre_division'] + ',' + cre_line[
                                      'account_code'] + ',' + cre_line['sub_account_code'] + ',' + cre_line[
                                      'depar_orga_code'] + ',,,,,,' + cre_line['partner_employee_division'] + ',' + \
                                  cre_line[
                                      'partner_employee_code'] + ',' + str(cre_line['journal_amount']) + ',' + str(
                        cre_line['tax_excluded_amount']) + ',' + str(cre_line['tax_amount']) + ',' + str(
                        cre_line['tax_id']) + ',' + cre_line[
                                      'tax_entry_division'] + ',' + summary1 + ',,,,,0,0,,,,,,,,,,,' + '\r\n'
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
        vals = {
            'name': 'SHIWAKE_SS' '.txt',
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
