# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round, float_is_zero
from datetime import datetime
import base64
from copy import deepcopy
import calendar


class SStreamJournalEntryOutput(models.TransientModel):
    _name = 'sstream.journal.entry.output'

    first_day_period = fields.Date(string='対象期間From')
    last_day_period = fields.Date(string='対象期間To')

    def get_a007_param(self):
        sstream_company_code = self.env['ir.config_parameter'].sudo().get_param('A007_super_stream_company_code')
        if not sstream_company_code:
            raise UserError('SuperStream連携用の会社コードの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_super_stream_company_code)')
        sstream_slip_group = self.env['ir.config_parameter'].sudo().get_param('A007_super_stream_slip_group')
        if not sstream_slip_group:
            raise UserError('SuperStream連携用の伝票グループの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_super_stream_slip_group)')

        product_ctg_merchandise = self.env['ir.config_parameter'].sudo().get_param('A007_product_ctg_merchandise')
        if not product_ctg_merchandise:
            raise UserError('プロダクトカテゴリ（商品）の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_product_ctg_merchandise)')

        product_ctg_product = self.env['ir.config_parameter'].sudo().get_param('A007_product_ctg_product')
        if not product_ctg_product:
            raise UserError('プロダクトカテゴリ（製品）の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_product_ctg_product)')

        product_ctg_material = self.env['ir.config_parameter'].sudo().get_param('A007_product_ctg_material')
        if not product_ctg_material:
            raise UserError('プロダクトカテゴリ（原材料）の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_product_ctg_material)')

        sanhot_point_product_id = self.env['ir.config_parameter'].sudo().get_param('A007_sanhot_point_product_id')
        if not sanhot_point_product_id:
            raise UserError('さんほっとポイントのプロダクトID取得に失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_sanhot_point_product_id)')

        product_ctg_stock = self.env['ir.config_parameter'].sudo().get_param('A007_product_ctg_product')
        if not product_ctg_stock:
            raise UserError('プロダクトカテゴリ（貯蔵品）の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_product_ctg_product)')

        sstream_linkage_recs = self.env['ss_erp.superstream.linkage.journal'].search(
            [('journal_creation', '=', 'odoo_journal')])
        if not sstream_linkage_recs:
            raise UserError('Odoo仕訳が見つかりませんでした。')

        result = {
            'sstream_company_code': sstream_company_code,
            'sstream_slip_group': sstream_slip_group,
            'product_ctg_merchandise': product_ctg_merchandise,
            'product_ctg_product': product_ctg_product,
            'product_ctg_material': product_ctg_material,
            'product_ctg_stock': product_ctg_stock,
            'sanhot_point_product_id': sanhot_point_product_id,
        }
        return result

    # with debit - no credit
    def query_pattern123(self, param):

        start_period = datetime.combine(self.first_day_period, datetime.min.time())
        end_period = datetime.combine(self.last_day_period, datetime.max.time())

        _select_data = f""" 
            WITH odoo_journal_linkage AS (
                SELECT * FROM ss_erp_superstream_linkage_journal where journal_creation = 'odoo_journal'								
            ),
            all_move_account AS (
                select
                    tb1.id as move_id
                    , string_agg(tb1.debit_account,', ') as debit_account
                    , string_agg(tb1.debit_sub_account,', ') as debit_sub_account
                    , string_agg(tb1.credit_account,', ') as credit_account
                    , string_agg(tb1.credit_sub_account,', ') as credit_sub_account
                    From
                    (select
                        am.id
                        , case when aml.debit>0 then aml.account_id::VARCHAR else Null end as debit_account
                        , case when aml.debit>0 then aml.x_sub_account_id::VARCHAR else Null end as debit_sub_account
                        , case when aml.credit>0 then aml.account_id::VARCHAR else Null end as credit_account
                        , case when aml.credit>0 then aml.x_sub_account_id::VARCHAR else Null end as credit_sub_account
                    from account_move_line aml
                    left join account_move am
                    on aml.move_id = am.id
                    Where
                    aml.is_super_stream_linked = False
                    ) tb1

                    group by tb1.id								
            )
            select									
                *						
            from(	
                select	
                 move_line_id
                ,product_id
                ,materials_grouping								
                ,record_division								
                , company_code								
                , slip_group
                , '' as slip_number
                , slip_date								
                , line_number								
                , deb_cre_division								
                , account_code								
                , sub_account_code								
                , depar_orga_code	
                , '' as function_code1								
                , '' as function_code2								
                , '' as function_code3								
                , '' as function_code4								
                , '' as project_code1	
                , partner_employee_division								
                , partner_employee_code								
                , journal_amount								
                , tax_excluded_amount								
                , tax_amount								
                , case when deb_cre_division = '1' then '000'								
                else tax_id								
                end as tax_id								
                , tax_entry_division								
                , summery1
                ,'' summery2	
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
                from 								
                (								
                    /* 消費税のある入庫請求仮とその消費税を取得する（借方-税計算なし） */								
                    select
                        aml.id as move_line_id
                        ,pt.id as product_id
                        ,'3' as record_division								
                        , '{param['sstream_company_code']}' as company_code								
                        , '{param['sstream_slip_group']}' as slip_group	
                        ,CASE 
                        WHEN ojl.slip_date_edit = 'first_day' THEN
                        to_char(date_trunc('month', am.date) + '-1 month', 'YYYY/MM/DD')
                        ELSE
                        to_char(date_trunc('month', am.date) + '1 month' + '-1 Day', 'YYYY/MM/DD')
                        END  as slip_date									
                        , '1' as line_number 								
                        , '0' as deb_cre_division								
                        , aa.code as account_code								
                        , COALESCE(seas.code, '') as sub_account_code								
                        ,  case when ojl.debit_department_edit_classification = 'no_edits' then serd.code || right(seo.organization_code, 3)
                        when ojl.debit_department_edit_classification = 'first_two_digits' then ojl.debit_accounting_department_code || right(seo.organization_code, 3)				
                        else ojl.debit_accounting_department_code								
                        end as depar_orga_code									
                        ,  case when ojl.debit_account_employee_category = 'no_used' then '0'
                        when ojl.debit_account_employee_category = 'custmer' then '1'				
                        when ojl.debit_account_employee_category = 'vendor' then '2'				
                        else '3'							
                        end as partner_employee_division										
                        , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                        ElSE '' END as partner_employee_code									
                        , seo.organization_code as organization_code								
                        , serd.code as department_code	
                        
                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                        sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END)	as journal_amount		
                        
                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                        sum(aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) as tax_excluded_amount	
                        
                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                        sum(aml.price_total - aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.price_total - aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) as tax_amount								

                        , aml_atr.account_tax_id as tax_id								
                        , '2' as tax_entry_division								
                        , pt.name as product	
                        , case when ojl.debit_application_edit_indicator = 'month' then aa.name || ' ' || to_char(am.date, 'MM') || '月分'
                        when ojl.debit_application_edit_indicator = 'month_and_branch' then aa.name || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        when ojl.debit_application_edit_indicator = 'org_from_to_month' then aa.name || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        ELSE aa.name || ' ' || to_char(am.date, 'MM') || pt.name || '月分/' || seo.name
                        END
                        as summery1
                        ,ojl.materials_grouping							
                    from								
                        account_move am /* 仕訳 */								
                        inner join								
                        account_move_line aml /* 仕訳項目 */								
                        on am.id = aml.move_id								
                        left join								
                        account_move_line_account_tax_rel aml_atr /* account_move_line_account_tax_rel */								
                        on aml.id = aml_atr.account_move_line_id								
                        left join 								
                        ss_erp_organization seo  /* 組織 */								
                        on am.x_organization_id = seo.id								
                        left join								
                        ss_erp_responsible_department serd /* 管轄部門 */								
                        on am.x_responsible_dept_id = serd.id								
                        left join								
                        account_account aa /* 勘定科目 */								
                        on aml.account_id = aa.id								
                        left join								
                        ss_erp_account_subaccount seas /* 補助科目 */								
                        on aml.x_sub_account_id = seas.id								
                        left join								
                        product_template pt  /* プロダクトテンプレート */								
                        on aml.product_id = pt.id
                        
                        left join all_move_account amc 
                        on amc.move_id = am.id
                        
                        left join odoo_journal_linkage ojl 
                        on ojl.debit_account = any(string_to_array(amc.debit_account, ',')::int[])	
                        and ojl.credit_account = any(string_to_array(amc.credit_account, ',')::int[])						
                        and (ojl.debit_sub_account is Null and amc.debit_sub_account is Null OR ojl.debit_sub_account = any(string_to_array(amc.debit_sub_account, ',')::int[]))					
                        and (ojl.credit_sub_account is Null and amc.credit_sub_account is Null OR ojl.credit_sub_account = any(string_to_array(amc.credit_sub_account, ',')::int[]))						
                    where								
                    pt.categ_id = any(string_to_array(ojl.categ_product_id_char, ',')::int[])
                    and aml.account_id = ojl.debit_account
                    and pt.id = any(string_to_array(ojl.sanhot_product_id_char, ',')::int[])
                    and aml.debit <> 0  /* 借方を取得 */								
                    and aml.parent_state = 'posted'  /* 記帳済み */								
                    and aml.is_super_stream_linked = False  /* SuperStream未連携 */								
                    and am.date BETWEEN '{start_period}' and '{end_period}'														
                                            
                union all								
                                                
                /* 消費税のある商品売上とその消費税を取得する（貸方-税計算あり） */								
                select 								
                    aml.id as move_line_id 
                    ,pt.id as product_id							
                    ,'3' as record_division								
                    , '{param['sstream_company_code']}' as company_code								
                    , '{param['sstream_slip_group']}' as slip_group								
                    ,CASE 
                    WHEN ojl.slip_date_edit = 'first_day' THEN
                    to_char(date_trunc('month', am.date) + '-1 month', 'YYYY/MM/DD')
                    ELSE
                    to_char(date_trunc('month', am.date) + '1 month' + '-1 Day', 'YYYY/MM/DD')
                    END  as slip_date									
                    , '2' as line_number 								
                    , '1' as deb_cre_division								
                    , cre_ojl.code as account_code								
                    , COALESCE(sub_cre_ojl.code, '') as sub_account_code								
                    ,  case when ojl.credit_department_editing_classification = 'no_edits' then serd.code || right(seo.organization_code, 3)
                    when ojl.credit_department_editing_classification = 'first_two_digits' then ojl.credit_accounting_department_code || right(seo.organization_code, 3)				
                    else ojl.credit_accounting_department_code								
                    end as depar_orga_code															
                    ,  case when ojl.credit_account_employee_category = 'no_used' then '0'
                    when ojl.credit_account_employee_category = 'custmer' then '1'				
                    when ojl.credit_account_employee_category = 'vendor' then '2'				
                    else '3'							
                    end as partner_employee_division												
                    , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                    ElSE '' END as partner_employee_code									
                    , seo.organization_code as organization_code								
                    , serd.code as department_code								
                        
                    , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                    sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                    ELSE sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END)	as journal_amount		
                    
                    , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                    sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                    ELSE sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) as tax_excluded_amount							
                    
                    , 0 as tax_amount								
                    , '000' as tax_id								
                    , '0' as tax_entry_division								
                    , pt.name as product
                    , case when ojl.credit_application_edit_indicator = 'month' then aa.name || ' ' || to_char(am.date, 'MM') || '月分'
                        when ojl.credit_application_edit_indicator = 'month_and_branch' then aa.name || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        when ojl.credit_application_edit_indicator = 'org_from_to_month' then aa.name || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        ELSE aa.name || ' ' || to_char(am.date, 'MM') || pt.name || '月分/' || seo.name
                        END
                        as summery1
                    ,ojl.materials_grouping									
                from								
                    account_move am /* 仕訳 */								
                    inner join								
                    account_move_line aml /* 仕訳項目 */								
                    on am.id = aml.move_id								
                    left join								
                    account_move_line_account_tax_rel aml_atr /* account_move_line_account_tax_rel */								
                    on aml.id = aml_atr.account_move_line_id								
                    left join 								
                    ss_erp_organization seo  /* 組織 */								
                    on am.x_organization_id = seo.id								
                    left join								
                    ss_erp_responsible_department serd /* 管轄部門 */								
                    on am.x_responsible_dept_id = serd.id								
                    left join								
                    account_account aa /* 勘定科目 */								
                    on aml.account_id = aa.id								
                    left join								
                    ss_erp_account_subaccount seas /* 補助科目 */								
                    on aml.x_sub_account_id = seas.id								
                    left join								
                    product_template pt  /* プロダクトテンプレート */								
                    on aml.product_id = pt.id		
                    
                    left join all_move_account amc 
                    on amc.move_id = am.id
                    
                    left join odoo_journal_linkage ojl 
                    on ojl.debit_account = any(string_to_array(amc.debit_account, ',')::int[])	
                    and ojl.credit_account = any(string_to_array(amc.credit_account, ',')::int[])						
                    and (ojl.debit_sub_account is Null and amc.debit_sub_account is Null OR ojl.debit_sub_account = any(string_to_array(amc.debit_sub_account, ',')::int[]))					
                    and (ojl.credit_sub_account is Null and amc.credit_sub_account is Null OR ojl.credit_sub_account = any(string_to_array(amc.credit_sub_account, ',')::int[]))	
                    
                    left join account_account cre_ojl 
                    on ojl.credit_account = cre_ojl.id	
                    left join ss_erp_account_subaccount sub_cre_ojl 
                    on ojl.credit_sub_account = sub_cre_ojl.id						
                where								
                pt.categ_id = any(string_to_array(ojl.categ_product_id_char, ',')::int[])
                and aml.account_id = ojl.debit_account
                and pt.id = any(string_to_array(ojl.sanhot_product_id_char, ',')::int[])								
                and aml.debit <> 0  /* 借方を取得 */								
                and aml.parent_state = 'posted'  /* 記帳済み */								
                and aml.is_super_stream_linked = False  /* SuperStream未連携 */								
                and am.date BETWEEN '{start_period}' and '{end_period}'	
                
                --START PATTERN2 NO DEBIT - WITH CREDIT
                UNION ALL
                select
                         aml.id as move_line_id  
                         ,pt.id as product_id 
                        ,'3' as record_division								
                        , '{param['sstream_company_code']}' as company_code								
                        , '{param['sstream_slip_group']}' as slip_group	
                        ,CASE WHEN ojl.slip_date_edit = 'first_day' THEN
                            to_char(date_trunc('month', am.date) + '-1 month', 'YYYY/MM/DD')
                            ELSE
                            to_char(date_trunc('month', am.date) + '1 month' + '-1 Day', 'YYYY/MM/DD')
                            END  as slip_date								
                        , '1' as line_number 								
                        , '0' as deb_cre_division								
                        , de_ojl.code as account_code								
                        , COALESCE(sub_de_ojl.code, '') as sub_account_code								
                        ,  case when ojl.debit_department_edit_classification = 'no_edits' then serd.code || right(seo.organization_code, 3)
                            when ojl.debit_department_edit_classification = 'first_two_digits' then ojl.debit_accounting_department_code || right(seo.organization_code, 3)				
                            else ojl.debit_accounting_department_code								
                            end as depar_orga_code								
                        ,  case when ojl.debit_account_employee_category = 'no_used' then '0'
                        when ojl.debit_account_employee_category = 'custmer' then '1'				
                        when ojl.debit_account_employee_category = 'vendor' then '2'				
                        else '3'							
                        end as partner_employee_division										
                        , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                            ElSE '' END as partner_employee_code					
                        , seo.organization_code as organization_code								
                        , serd.code as department_code
                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 								
                        sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END)	as journal_amount		
                        
                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                        sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) as tax_excluded_amount								
                        , 0 as tax_amount								
                        , aml_atr.account_tax_id as tax_id								
                        , '2' as tax_entry_division								
                        , pt.name as product
                        , case when ojl.debit_application_edit_indicator = 'month' then aa.name || ' ' || to_char(am.date, 'MM') || '月分'
                        when ojl.debit_application_edit_indicator = 'month_and_branch' then aa.name || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        when ojl.debit_application_edit_indicator = 'org_from_to_month' then aa.name || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        ELSE aa.name || ' ' || to_char(am.date, 'MM') || pt.name || '月分/' || seo.name
                        END
                        as summery1	
                        ,ojl.materials_grouping		
                        
                    from								
                        account_move am /* 仕訳 */								
                        inner join								
                        account_move_line aml /* 仕訳項目 */								
                        on am.id = aml.move_id								
                        left join								
                        account_move_line_account_tax_rel aml_atr /* account_move_line_account_tax_rel */								
                        on aml.id = aml_atr.account_move_line_id								
                        left join 								
                        ss_erp_organization seo  /* 組織 */								
                        on am.x_organization_id = seo.id								
                        left join								
                        ss_erp_responsible_department serd /* 管轄部門 */								
                        on am.x_responsible_dept_id = serd.id								
                        left join								
                        account_account aa /* 勘定科目 */								
                        on aml.account_id = aa.id								
                        left join								
                        ss_erp_account_subaccount seas /* 補助科目 */								
                        on aml.x_sub_account_id = seas.id								
                        left join								
                        product_template pt  /* プロダクトテンプレート */								
                        on aml.product_id = pt.id
                        
                        left join all_move_account amc 
                        on amc.move_id = am.id
                        
                        left join odoo_journal_linkage ojl 
                        on ojl.debit_account = any(string_to_array(amc.debit_account, ',')::int[])	
                        and ojl.credit_account = any(string_to_array(amc.credit_account, ',')::int[])						
                        and (ojl.debit_sub_account is Null and amc.debit_sub_account is Null OR ojl.debit_sub_account = any(string_to_array(amc.debit_sub_account, ',')::int[]))					
                        and (ojl.credit_sub_account is Null and amc.credit_sub_account is Null OR ojl.credit_sub_account = any(string_to_array(amc.credit_sub_account, ',')::int[]))		

                        left join account_account de_ojl 
                        on ojl.debit_account = de_ojl.id	
                        left join ss_erp_account_subaccount sub_de_ojl 
                        on ojl.debit_sub_account = sub_de_ojl.id						
                    where								
                    pt.categ_id = any(string_to_array(ojl.categ_product_id_char, ',')::int[])
                    and aml.account_id = ojl.credit_account
                    and pt.id = any(string_to_array(ojl.sanhot_product_id_char, ',')::int[])									
                    and aml.credit <> 0  /* 借方を取得 */								
                    and aml.parent_state = 'posted'  /* 記帳済み */								
                    and aml.is_super_stream_linked = False  /* SuperStream未連携 */								
                    and am.date BETWEEN '{start_period}' and '{end_period}'														
                                            
                union all								
                                                
                /* 消費税のある商品売上とその消費税を取得する（貸方-税計算あり） */								
                select 								
                    aml.id as move_line_id
                    ,pt.id as product_id
                    ,'3' as record_division								
                    , '{param['sstream_company_code']}' as company_code								
                    , '{param['sstream_slip_group']}' as slip_group								
                    ,CASE WHEN ojl.slip_date_edit = 'first_day' THEN
                        to_char(date_trunc('month', am.date) + '-1 month', 'YYYY/MM/DD')
                        ELSE
                        to_char(date_trunc('month', am.date) + '1 month' + '-1 Day', 'YYYY/MM/DD')
                        END  as slip_date									
                    , '2' as line_number 								
                    , '1' as deb_cre_division								
                    , aa.code as account_code								
                    , COALESCE(seas.code, '') as sub_account_code								
                    ,  case when ojl.credit_department_editing_classification = 'no_edits' then serd.code || right(seo.organization_code, 3)
                    when ojl.credit_department_editing_classification = 'first_two_digits' then ojl.credit_accounting_department_code || right(seo.organization_code, 3)				
                    else ojl.credit_accounting_department_code								
                    end as depar_orga_code									
                    ,  case when ojl.credit_account_employee_category = 'no_used' then '0'
                    when ojl.credit_account_employee_category = 'custmer' then '1'				
                    when ojl.credit_account_employee_category = 'vendor' then '2'				
                    else '3'							
                    end as partner_employee_division										
                    , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                        ElSE '' END as partner_employee_code								
                    , seo.organization_code as organization_code								
                    , serd.code as department_code								
                    , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                    sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                    ELSE sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END)	as journal_amount		
                    
                    , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                    sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                    ELSE sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) as tax_excluded_amount								
                    , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                    sum(aml.price_total - aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                    ELSE sum(aml.price_total - aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) as tax_amount									
                    , '000' as tax_id								
                    , '0' as tax_entry_division								
                    , pt.name as product	
                    , case when ojl.credit_application_edit_indicator = 'month' then aa.name || ' ' || to_char(am.date, 'MM') || '月分'
                    when ojl.credit_application_edit_indicator = 'month_and_branch' then aa.name || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                    when ojl.credit_application_edit_indicator = 'org_from_to_month' then aa.name || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                    ELSE aa.name || ' ' || to_char(am.date, 'MM') || pt.name || '月分/' || seo.name
                    END
                    as summery1
                    ,ojl.materials_grouping					
                from								
                    account_move am /* 仕訳 */								
                    inner join								
                    account_move_line aml /* 仕訳項目 */								
                    on am.id = aml.move_id								
                    left join								
                    account_move_line_account_tax_rel aml_atr /* account_move_line_account_tax_rel */								
                    on aml.id = aml_atr.account_move_line_id								
                    left join 								
                    ss_erp_organization seo  /* 組織 */								
                    on am.x_organization_id = seo.id								
                    left join								
                    ss_erp_responsible_department serd /* 管轄部門 */								
                    on am.x_responsible_dept_id = serd.id								
                    left join								
                    account_account aa /* 勘定科目 */								
                    on aml.account_id = aa.id								
                    left join								
                    ss_erp_account_subaccount seas /* 補助科目 */								
                    on aml.x_sub_account_id = seas.id								
                    left join								
                    product_template pt  /* プロダクトテンプレート */								
                    on aml.product_id = pt.id	
                    
                    left join all_move_account amc 
                    on amc.move_id = am.id
                    
                    left join odoo_journal_linkage ojl 
                    on ojl.debit_account = any(string_to_array(amc.debit_account, ',')::int[])	
                    and ojl.credit_account = any(string_to_array(amc.credit_account, ',')::int[])						
                    and (ojl.debit_sub_account is Null and amc.debit_sub_account is Null OR ojl.debit_sub_account = any(string_to_array(amc.debit_sub_account, ',')::int[]))					
                    and (ojl.credit_sub_account is Null and amc.credit_sub_account is Null OR ojl.credit_sub_account = any(string_to_array(amc.credit_sub_account, ',')::int[]))								
                where								
                pt.categ_id = any(string_to_array(ojl.categ_product_id_char, ',')::int[])
                and aml.account_id = ojl.credit_account
                and pt.id = any(string_to_array(ojl.sanhot_product_id_char, ',')::int[])									
                and aml.credit <> 0  /* 借方を取得 */								
                and aml.parent_state = 'posted'  /* 記帳済み */								
                and aml.is_super_stream_linked = False  /* SuperStream未連携 */								
                and am.date BETWEEN '{start_period}' and '{end_period}'																
                
                --end pattern2

                --START PATTERN3 NO DEBIT - NO CREDIT
                UNION ALL
                    /* 消費税のある入庫請求仮とその消費税を取得する（借方-税計算なし） */								
                    select
                         aml.id as move_line_id 
                         ,pt.id as product_id  
                        ,'3' as record_division								
                        , '{param['sstream_company_code']}' as company_code								
                        , '{param['sstream_slip_group']}' as slip_group	
                       ,CASE WHEN ojl.slip_date_edit = 'first_day' THEN
                        to_char(date_trunc('month', am.date) + '-1 month', 'YYYY/MM/DD')
                        ELSE
                        to_char(date_trunc('month', am.date) + '1 month' + '-1 Day', 'YYYY/MM/DD')
                        END  as slip_date										
                        , '1' as line_number 								
                        , '0' as deb_cre_division								
                        , aa.code as account_code								
                        , COALESCE(seas.code, '') as sub_account_code								
                        ,  case when ojl.debit_department_edit_classification = 'no_edits' then serd.code || right(seo.organization_code, 3)
                        when ojl.debit_department_edit_classification = 'first_two_digits' then ojl.debit_accounting_department_code || right(seo.organization_code, 3)				
                        else ojl.debit_accounting_department_code								
                        end as depar_orga_code									
                        ,  case when ojl.debit_account_employee_category = 'no_used' then '0'
                        when ojl.debit_account_employee_category = 'custmer' then '1'				
                        when ojl.debit_account_employee_category = 'vendor' then '2'				
                        else '3'							
                        end as partner_employee_division								
                        , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                        ElSE '' END as partner_employee_code									
                        , seo.organization_code as organization_code								
                        , serd.code as department_code								
                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                        sum(aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END)	as journal_amount		
                        
                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                        sum(aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) as tax_excluded_amount							
                        , 0 as tax_amount								
                        , aml_atr.account_tax_id as tax_id								
                        , '2' as tax_entry_division								
                        , pt.name as product	
                        , case when ojl.debit_application_edit_indicator = 'month' then aa.name || ' ' || to_char(am.date, 'MM') || '月分'
                        when ojl.debit_application_edit_indicator = 'month_and_branch' then aa.name || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        when ojl.debit_application_edit_indicator = 'org_from_to_month' then aa.name || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        ELSE aa.name || ' ' || to_char(am.date, 'MM') || pt.name || '月分/' || seo.name
                        END
                        as summery1	
                        ,ojl.materials_grouping									
                    from								
                        account_move am /* 仕訳 */								
                        inner join								
                        account_move_line aml /* 仕訳項目 */								
                        on am.id = aml.move_id								
                        left join								
                        account_move_line_account_tax_rel aml_atr /* account_move_line_account_tax_rel */								
                        on aml.id = aml_atr.account_move_line_id								
                        left join 								
                        ss_erp_organization seo  /* 組織 */								
                        on am.x_organization_id = seo.id								
                        left join								
                        ss_erp_responsible_department serd /* 管轄部門 */								
                        on am.x_responsible_dept_id = serd.id								
                        left join								
                        account_account aa /* 勘定科目 */								
                        on aml.account_id = aa.id								
                        left join								
                        ss_erp_account_subaccount seas /* 補助科目 */								
                        on aml.x_sub_account_id = seas.id								
                        left join								
                        product_template pt  /* プロダクトテンプレート */								
                        on aml.product_id = pt.id	
                        
                        left join all_move_account amc 
                        on amc.move_id = am.id
                        
                        left join odoo_journal_linkage ojl 
                        on ojl.debit_account = any(string_to_array(amc.debit_account, ',')::int[])	
                        and ojl.credit_account = any(string_to_array(amc.credit_account, ',')::int[])						
                        and (ojl.debit_sub_account is Null and amc.debit_sub_account is Null OR ojl.debit_sub_account = any(string_to_array(amc.debit_sub_account, ',')::int[]))					
                        and (ojl.credit_sub_account is Null and amc.credit_sub_account is Null OR ojl.credit_sub_account = any(string_to_array(amc.credit_sub_account, ',')::int[]))								
                    where								
                    pt.categ_id = any(string_to_array(ojl.categ_product_id_char, ',')::int[])
                    and aml.account_id = ojl.debit_account
                    and aml.price_total = aml.price_subtotal
                    and pt.id = any(string_to_array(ojl.sanhot_product_id_char, ',')::int[])								
                    and aml.debit <> 0  /* 借方を取得 */								
                    and aml.parent_state = 'posted'  /* 記帳済み */								
                    and aml.is_super_stream_linked = False  /* SuperStream未連携 */								
                    and am.date BETWEEN '{start_period}' and '{end_period}'														
                                            
                union all								
                                                
                /* 消費税のある商品売上とその消費税を取得する（貸方-税計算あり） */								
                select 								
                    aml.id as move_line_id
                    ,pt.id as product_id
                    ,'3' as record_division								
                    , '{param['sstream_company_code']}' as company_code								
                    , '{param['sstream_slip_group']}' as slip_group								
                   ,CASE WHEN ojl.slip_date_edit = 'first_day' THEN
                    to_char(date_trunc('month', am.date) + '-1 month', 'YYYY/MM/DD')
                    ELSE
                    to_char(date_trunc('month', am.date) + '1 month' + '-1 Day', 'YYYY/MM/DD')
                    END  as slip_date										
                    , '2' as line_number 								
                    , '1' as deb_cre_division								
                    , aa.code as account_code								
                    , COALESCE(seas.code, '') as sub_account_code								
                    ,  case when ojl.credit_department_editing_classification = 'no_edits' then serd.code || right(seo.organization_code, 3)
                    when ojl.credit_department_editing_classification = 'first_two_digits' then ojl.credit_accounting_department_code || right(seo.organization_code, 3)				
                    else ojl.credit_accounting_department_code								
                    end as depar_orga_code									
                    ,  case when ojl.credit_account_employee_category = 'no_used' then '0'
                    when ojl.credit_account_employee_category = 'custmer' then '1'				
                    when ojl.credit_account_employee_category = 'vendor' then '2'				
                    else '3'							
                    end as partner_employee_division									
                    , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                    ElSE '' END as partner_employee_code								
                    , seo.organization_code as organization_code								
                    , serd.code as department_code								
                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                        sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END)	as journal_amount		
                        
                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                        sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) as tax_excluded_amount								
                    , 0 as tax_amount								
                    , '000' as tax_id								
                    , '0' as tax_entry_division								
                    , pt.name as product
                    , case when ojl.credit_application_edit_indicator = 'month' then aa.name || ' ' || to_char(am.date, 'MM') || '月分'
                    when ojl.credit_application_edit_indicator = 'month_and_branch' then aa.name || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                    when ojl.credit_application_edit_indicator = 'org_from_to_month' then aa.name || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                    ELSE aa.name || ' ' || to_char(am.date, 'MM') || pt.name || '月分/' || seo.name
                    END
                    as summery1	
                    ,ojl.materials_grouping								
                from								
                    account_move am /* 仕訳 */								
                    inner join								
                    account_move_line aml /* 仕訳項目 */								
                    on am.id = aml.move_id								
                    left join								
                    account_move_line_account_tax_rel aml_atr /* account_move_line_account_tax_rel */								
                    on aml.id = aml_atr.account_move_line_id								
                    left join 								
                    ss_erp_organization seo  /* 組織 */								
                    on am.x_organization_id = seo.id								
                    left join								
                    ss_erp_responsible_department serd /* 管轄部門 */								
                    on am.x_responsible_dept_id = serd.id								
                    left join								
                    account_account aa /* 勘定科目 */								
                    on aml.account_id = aa.id								
                    left join								
                    ss_erp_account_subaccount seas /* 補助科目 */								
                    on aml.x_sub_account_id = seas.id								
                    inner join								
                    product_template pt  /* プロダクトテンプレート */								
                    on aml.product_id = pt.id	
                    
                    left join all_move_account amc 
                    on amc.move_id = am.id
                    
                    left join odoo_journal_linkage ojl 
                    on ojl.debit_account = any(string_to_array(amc.debit_account, ',')::int[])	
                    and ojl.credit_account = any(string_to_array(amc.credit_account, ',')::int[])						
                    and (ojl.debit_sub_account is Null and amc.debit_sub_account is Null OR ojl.debit_sub_account = any(string_to_array(amc.debit_sub_account, ',')::int[]))					
                    and (ojl.credit_sub_account is Null and amc.credit_sub_account is Null OR ojl.credit_sub_account = any(string_to_array(amc.credit_sub_account, ',')::int[]))								
                where								
                pt.categ_id = any(string_to_array(ojl.categ_product_id_char, ',')::int[])
                and aml.account_id = ojl.credit_account
                and aml.price_total = aml.price_subtotal
                and pt.id = any(string_to_array(ojl.sanhot_product_id_char, ',')::int[])								
                and aml.credit <> 0  /* 借方を取得 */								
                and aml.parent_state = 'posted'  /* 記帳済み */								
                and aml.is_super_stream_linked = False  /* SuperStream未連携 */								
                and am.date BETWEEN '{start_period}' and '{end_period}'																
                --end pattern3											
                ) result								
                order by								
                   product asc								
                    , organization_code asc								
                    , department_code asc								
                    , tax_id asc  								
                    , deb_cre_division asc								
                    , line_number asc  								
            )pattern123								

        """
        self._cr.execute(_select_data)
        data_pattern123 = self._cr.dictfetchall()
        return data_pattern123

    # transfer between branch
    def query_pattern5(self, param):

        start_period = datetime.combine(self.first_day_period, datetime.min.time())
        end_period = datetime.combine(self.last_day_period, datetime.max.time())

        _select_data = f"""
        WITH odoo_journal_linkage AS (
            SELECT * FROM ss_erp_superstream_linkage_journal where journal_creation = 'transfer_between_bases'								
            )
        select 						
            *				
            from (
                select
                    inventory_order_line_id								
                    ,product_id	
                    ,materials_grouping							
                    ,record_division								
                    , company_code								
                    , slip_group
                    , '' as slip_number
                    , slip_date								
                    , line_number								
                    , deb_cre_division								
                    , account_code								
                    , sub_account_code								
                    , depar_orga_code	
                    , '' as function_code1								
                    , '' as function_code2								
                    , '' as function_code3								
                    , '' as function_code4								
                    , '' as project_code1	
                    , partner_employee_division								
                    , partner_employee_code								
                    , journal_amount								
                    , tax_excluded_amount								
                    , tax_amount								
                    , case when deb_cre_division = '1' then '000'								
                    else tax_id								
                    end as tax_id								
                    , tax_entry_division								
                    , summery1
                    ,'' summery2	
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
                from					
                (						
                    select								
                        iol.id inventory_order_line_id -- 		just a column to shorten the code below	
                        ,pp.id as product_id
                        ,ojl.materials_grouping
                        ,'3' as record_division								
                        , '{param['sstream_company_code']}' as company_code								
                        , '{param['sstream_slip_group']}' as slip_group
                        , CASE WHEN ojl.slip_date_edit = 'first_day' THEN
                        to_char(date_trunc('month', sp.date) + '-1 month', 'YYYY/MM/DD')
                        ELSE
                        to_char(date_trunc('month', sp.date) + '1 month' + '-1 Day', 'YYYY/MM/DD')
                        END  as slip_date			
                        , '1' as line_number 								
                        , '0' as deb_cre_division	
                        , de_ojl.code as account_code								
                        , COALESCE(sub_de_ojl.code, '') as sub_account_code	
                        ,  case when ojl.debit_department_edit_classification = 'no_edits' then serd.code || right(seo.organization_code, 3)
                        when ojl.debit_department_edit_classification = 'first_two_digits' then ojl.credit_accounting_department_code || right(seo.organization_code, 3)				
                        else ojl.debit_accounting_department_code								
                        end as depar_orga_code	
                        ,  case when ojl.debit_account_employee_category = 'no_used' then '0'
                        when ojl.debit_account_employee_category = 'custmer' then '1'				
                        when ojl.debit_account_employee_category = 'vendor' then '2'				
                        else '3'							
                        end as partner_employee_division			
                        , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                        ElSE '' END as partner_employee_code	
                        ,seo.organization_code as organization_code	
                        , serd.code as department_code
                        ,sum(iol.product_uom_qty * prop.value_float) OVER (PARTITION BY sp.date,seo.organization_code, serd.code) as journal_amount		
                        ,sum(iol.product_uom_qty * prop.value_float) OVER (PARTITION BY sp.date,seo.organization_code, serd.code) as tax_excluded_amount	
                        , 0 as tax_amount						
                        , '000' as tax_id						
                        , '0' as tax_entry_division	
                        , case when ojl.debit_application_edit_indicator = 'month' then de_ojl.name || ' ' || to_char(sp.date, 'MM') || '月分'
                            when ojl.debit_application_edit_indicator = 'month_and_branch' then de_ojl.name || ' ' || to_char(sp.date, 'MM') || '月分/' || seo.name 
                            when ojl.debit_application_edit_indicator = 'org_from_to_month' then de_ojl.name || '/' || source_seo.name || '->' || dest_seo.name || to_char(sp.date, 'MM') || '月分'
                            when ojl.debit_application_edit_indicator = 'dept_from_to_month' then de_ojl.name || '/' || source_seo.name || '->' || dest_seo.name || to_char(sp.date, 'MM') || '月分'
                            ELSE de_ojl.name || ' ' || to_char(sp.date, 'MM') || pt.name || '月分/' || seo.name
                            END
                            as summery1
                    from						
                        ss_erp_inventory_order io  /* 移動伝票 */						
                        inner join						
                        ss_erp_inventory_order_line iol  /* 移動伝票明細 */						
                        on io.id = iol.order_id						
                        left join						
                        stock_picking sp  /* 運送 */						
                        on io.id = sp.x_inventory_order_id						
                        left join	
                        ss_erp_responsible_department serd /* 管轄部門 */						
                        on sp.x_responsible_dept_id = serd.id						
                        left join						
                        ss_erp_organization seo /* 組織 */						
                        on sp.x_organization_id = seo.id						
                        left join						
                        product_product pp  /* プロダクト */						
                        on iol.product_id = pp.id
                        left join product_template pt on pp.product_tmpl_id = pt.id
                        left join ir_property prop on prop.res_id = 'product.product,' || pp.id		
        
                        left join odoo_journal_linkage ojl 
                        on io.organization_id = ojl.credit_related_organization and iol.organization_id = ojl.debit_related_organization
                        left join account_account de_ojl 
                        on ojl.debit_account = de_ojl.id	
                        left join ss_erp_account_subaccount sub_de_ojl 
                        on ojl.debit_sub_account = sub_de_ojl.id
                        
                        left join ss_erp_organization source_seo
                        on ojl.debit_related_organization = source_seo.id
                        left join ss_erp_organization dest_seo
                        on ojl.credit_related_organization = dest_seo.id

                    where						
                    sp.state = 'done'  /* 完了を指定 */						
                    and sp.date BETWEEN '{start_period}' and '{end_period}'					
                    and sp.x_organization_id = ojl.credit_related_organization  /* 移動元組織（貸方関連組織を指定） */						
                    and sp.x_organization_dest_id = ojl.debit_related_organization /* 移動先組織（借方関連組織を指定） */	
                    and io.is_super_stream_linked = False																			
                                                                                                         
            union all						
        
                select								
                    iol.id inventory_order_line_id -- 		just a column to shorten the code below	
                    ,pp.id as product_id
                    ,ojl.materials_grouping
                    ,'3' as record_division								
                    , '{param['sstream_company_code']}' as company_code								
                    , '{param['sstream_slip_group']}' as slip_group
                    , CASE WHEN ojl.slip_date_edit = 'first_day' THEN
                    to_char(date_trunc('month', sp.date) + '-1 month', 'YYYY/MM/DD')
                    ELSE
                    to_char(date_trunc('month', sp.date) + '1 month' + '-1 Day', 'YYYY/MM/DD')
                    END  as slip_date			
                    , '1' as line_number 								
                    , '0' as deb_cre_division	
                    , cre_ojl.code as account_code								
                    , COALESCE(sub_cre_ojl.code, '') as sub_account_code	
                    ,  case when ojl.credit_department_editing_classification = 'no_edits' then serd.code || right(seo.organization_code, 3)
                    when ojl.credit_department_editing_classification = 'first_two_digits' then ojl.credit_accounting_department_code || right(seo.organization_code, 3)				
                    else ojl.credit_accounting_department_code								
                    end as depar_orga_code	
                    ,  case when ojl.credit_account_employee_category = 'no_used' then '0'
                    when ojl.credit_account_employee_category = 'custmer' then '1'				
                    when ojl.credit_account_employee_category = 'vendor' then '2'				
                    else '3'							
                    end as partner_employee_division			
                    , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                    ElSE '' END as partner_employee_code	
                    ,seo.organization_code as organization_code	
                    , serd.code as department_code
                    ,sum(iol.product_uom_qty * prop.value_float) OVER (PARTITION BY sp.date,seo.organization_code, serd.code) as journal_amount		
                    ,sum(iol.product_uom_qty * prop.value_float) OVER (PARTITION BY sp.date,seo.organization_code, serd.code) as tax_excluded_amount	
                    , 0 as tax_amount						
                    , '000' as tax_id						
                    , '0' as tax_entry_division	
                    , case when ojl.debit_application_edit_indicator = 'month' then cre_ojl.name || ' ' || to_char(sp.date, 'MM') || '月分'
                        when ojl.debit_application_edit_indicator = 'month_and_branch' then cre_ojl.name || ' ' || to_char(sp.date, 'MM') || '月分/' || seo.name 
                        when ojl.debit_application_edit_indicator = 'org_from_to_month' then cre_ojl.name || '/' || source_seo.name || '->' || dest_seo.name || to_char(sp.date, 'MM') || '月分'
                        when ojl.debit_application_edit_indicator = 'dept_from_to_month' then cre_ojl.name || '/' || source_seo.name || '->' || dest_seo.name || to_char(sp.date, 'MM') || '月分'
                        ELSE cre_ojl.name || ' ' || to_char(sp.date, 'MM') || pt.name || '月分/' || seo.name
                        END
                        as summery1									
                from						
                    ss_erp_inventory_order io  /* 移動伝票 */						
                    inner join						
                    ss_erp_inventory_order_line iol  /* 移動伝票明細 */						
                    on io.id = iol.order_id						
                    left join						
                    stock_picking sp  /* 運送 */						
                    on io.id = sp.x_inventory_order_id						
                    left join						
                    ss_erp_responsible_department serd /* 管轄部門 */						
                    on sp.x_responsible_dept_id = serd.id						
                    left join						
                    ss_erp_organization seo /* 組織 */						
                    on sp.x_organization_id = seo.id						
                    left join						
                    product_product pp  /* プロダクト */						
                    on iol.product_id = pp.id
                    left join product_template pt on pp.product_tmpl_id = pt.id
                    left join ir_property prop on prop.res_id = 'product.product,' || pp.id		
                            
                    left join odoo_journal_linkage ojl 
                    on io.organization_id = ojl.credit_related_organization and iol.organization_id = ojl.debit_related_organization	
                    left join account_account cre_ojl 
                    on ojl.credit_account = cre_ojl.id	
                    left join ss_erp_account_subaccount sub_cre_ojl 
                    on ojl.credit_sub_account = sub_cre_ojl.id	
                    
                    left join ss_erp_organization source_seo
                    on ojl.debit_related_organization = source_seo.id
                    left join ss_erp_organization dest_seo
                    on ojl.credit_related_organization = dest_seo.id			
                where						
                sp.state = 'done'  /* 完了を指定 */						
                and sp.date BETWEEN '{start_period}' and '{end_period}'							
                and sp.x_organization_id = ojl.credit_related_organization  /* 移動元組織（貸方関連組織を指定） */						
                and sp.x_organization_dest_id = ojl.debit_related_organization /* 移動先組織（借方関連組織を指定） */	
                and io.is_super_stream_linked = False	
            ) result				
                order by						
                department_code asc						
                , deb_cre_division asc						
                , line_number asc	
                )pattern5										
"""
        self._cr.execute(_select_data)
        data_pattern5 = self._cr.dictfetchall()
        return data_pattern5

    def export_sstream_journal_entry(self):
        # Captured data start record
        file_data = "0,1" + '\r\n'

        param = self.get_a007_param()

        pattern123_data = self.query_pattern123(param)
        #
        pattern5_data = self.query_pattern5(param)

        all_pattern_data = pattern123_data + pattern5_data

        debit_line_data = []
        credit_line_data = []
        for pd in all_pattern_data:
            if pd['deb_cre_division'] == '0':
                debit_line_data.append(pd)
            else:
                credit_line_data.append(pd)

        list_group = []
        for de_line in debit_line_data:
            if de_line['materials_grouping']:
                if list_group == [de_line['slip_date'], de_line['depar_orga_code'], de_line['account_code'], de_line['sub_account_code'], de_line['product_id'] ]:
                    continue
                else:
                    list_group = [de_line['slip_date'], de_line['depar_orga_code'], de_line['account_code'], de_line['sub_account_code'], de_line['product_id'] ]

            if de_line.get('move_line_id'):
                move_line_rec = self.env['account.move.line'].browse(de_line['move_line_id'])
                move_line_rec.is_super_stream_linked = True
            if de_line.get('inventory_order_line_id'):
                iol_rec = self.env['ss_erp.inventory.order.line'].browse(de_line['inventory_order_line_id'])
                iol_rec.order_id.is_super_stream_linked = True

            # Document data header record
            doc_header = "1" + '\r\n'
            file_data += doc_header

            # journal entry header region
            journal_header = "2," + param['sstream_company_code'] + "," + param['sstream_slip_group'] + ",," + de_line[
                'slip_date'] + ',,0,1,,,,,0,0,,,,,,,,,,,,,' + '\r\n'
            file_data += journal_header

            debit_line = ''
            credit_line = ''
            # tax region
            if de_line['tax_id'] != '000':
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

                de_line['tax_id'] = convert_tax_map.external_code or de_line['tax_id']
            clean_dict_data = deepcopy(de_line)
            if clean_dict_data.get('move_line_id'):
                clean_dict_data.pop('move_line_id')
            if clean_dict_data.get('materials_grouping') is not None:
                clean_dict_data.pop('materials_grouping')
            if clean_dict_data.get('product_id') is not None:
                clean_dict_data.pop('product_id')
            if clean_dict_data.get('inventory_order_line_id'):
                clean_dict_data.pop('inventory_order_line_id')
            debit_line = ','.join(map(str, clean_dict_data.values())) + '\r\n'

            for cre_line in credit_line_data:

                if cre_line['move_line_id'] == de_line['move_line_id']:
                    clean_dict_data = deepcopy(cre_line)
                    if clean_dict_data.get('move_line_id'):
                        clean_dict_data.pop('move_line_id')
                    if clean_dict_data.get('materials_grouping') is not None:
                        clean_dict_data.pop('materials_grouping')
                    if clean_dict_data.get('product_id') is not None:
                        clean_dict_data.pop('product_id')
                    if clean_dict_data.get('inventory_order_line_id'):
                        clean_dict_data.pop('inventory_order_line_id')
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
