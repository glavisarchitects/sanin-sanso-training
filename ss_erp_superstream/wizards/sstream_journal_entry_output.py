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
            raise UserError(
                'SuperStream連携用の会社コードの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_super_stream_company_code)')
        sstream_slip_group = self.env['ir.config_parameter'].sudo().get_param('A007_super_stream_slip_group')
        if not sstream_slip_group:
            raise UserError(
                'SuperStream連携用の伝票グループの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_super_stream_slip_group)')

        product_ctg_merchandise = self.env['ir.config_parameter'].sudo().get_param('A007_product_ctg_merchandise')
        if not product_ctg_merchandise:
            raise UserError(
                'プロダクトカテゴリ（商品）の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_product_ctg_merchandise)')

        product_ctg_product = self.env['ir.config_parameter'].sudo().get_param('A007_product_ctg_product')
        if not product_ctg_product:
            raise UserError(
                'プロダクトカテゴリ（製品）の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_product_ctg_product)')

        product_ctg_material = self.env['ir.config_parameter'].sudo().get_param('A007_product_ctg_material')
        if not product_ctg_material:
            raise UserError(
                'プロダクトカテゴリ（原材料）の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_product_ctg_material)')

        sanhot_point_product_id = self.env['ir.config_parameter'].sudo().get_param('A007_sanhot_point_product_id')
        if not sanhot_point_product_id:
            raise UserError(
                'さんほっとポイントのプロダクトID取得に失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_sanhot_point_product_id)')

        product_ctg_stock = self.env['ir.config_parameter'].sudo().get_param('A007_product_ctg_stock')
        if not product_ctg_stock:
            raise UserError(
                'プロダクトカテゴリ（貯蔵品）の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_product_ctg_stock")')

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
    def query_pattern12(self, param):

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
                , journal_amount :: BIGINT								
                , tax_excluded_amount :: BIGINT							
                , tax_amount :: BIGINT								
                , case when deb_cre_division = '1' then '000'								
                else COALESCE(tax_id, 0)								
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
                        when ojl.debit_account_employee_category = 'customer' then '1'				
                        when ojl.debit_account_employee_category = 'vendor' then '2'				
                        else '3'							
                        end as partner_employee_division										
                        , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                        ElSE '' END as partner_employee_code									
                        , seo.organization_code as organization_code								
                        , serd.code as department_code	
                        
                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                        sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) :: BIGINT as journal_amount		
                        
                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                        sum(aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) :: BIGINT as tax_excluded_amount	
                        
                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                        sum(aml.price_total - aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.price_total - aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) as tax_amount								

                        , aml_atr.account_tax_id as tax_id								
                        , '2' as tax_entry_division								
                        , pt.name as product	
                        , case when ojl.debit_application_edit_indicator = 'month' then ojl.debit_application || ' ' || to_char(am.date, 'MM') || '月分'
                        when ojl.debit_application_edit_indicator = 'month_and_branch' then ojl.debit_application || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        when ojl.debit_application_edit_indicator = 'org_from_to_month' then ojl.debit_application || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        ELSE ojl.debit_application || ' ' || to_char(am.date, 'MM') || pt.name || '月分/' || seo.name
                        END
                        as summery1
                        ,ojl.materials_grouping
                    from				
                        account_move_line aml /* 仕訳項目 */
                        left join								                        					
                        account_move am /* 仕訳 */								                        							
                        on am.id = aml.move_id								
                        inner join								
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
                        and (ojl.debit_sub_account is Null and aml.x_sub_account_id is Null OR ojl.debit_sub_account = any(string_to_array(amc.debit_sub_account, ',')::int[]))					
                        and (ojl.credit_sub_account is Null and aml.x_sub_account_id is Null OR ojl.credit_sub_account = any(string_to_array(amc.credit_sub_account, ',')::int[]))							
                    where								
                    aml.account_id = ojl.debit_account								
                    and (pt.categ_id is Null or pt.categ_id = any(string_to_array(ojl.categ_product_id_char, ',')::int[]) )  
                    and (pt.id is Null or pt.id = any(string_to_array(ojl.sanhot_product_id_char, ',')::int[]))	
                    and aml.debit <> 0  /* 借方を取得 */								
                    and aml.parent_state = 'posted'  /* 記帳済み */								
                    and aml.product_id is not Null							
                    and ojl.debit_tax_calculation = True	
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
                    when ojl.credit_account_employee_category = 'customer' then '1'				
                    when ojl.credit_account_employee_category = 'vendor' then '2'				
                    else '3'							
                    end as partner_employee_division												
                    , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                    ElSE '' END as partner_employee_code									
                    , seo.organization_code as organization_code								
                    , serd.code as department_code								
                        
                    , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                    sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                    ELSE sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) :: BIGINT as journal_amount		
                    
                    , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                    sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                    ELSE sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) :: BIGINT as tax_excluded_amount							
                    
                    , 0 as tax_amount								
                    , '000' as tax_id								
                    , '0' as tax_entry_division								
                    , pt.name as product
                    , case when ojl.credit_application_edit_indicator = 'month' then ojl.credit_application || ' ' || to_char(am.date, 'MM') || '月分'
                        when ojl.credit_application_edit_indicator = 'month_and_branch' then ojl.credit_application || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        when ojl.credit_application_edit_indicator = 'org_from_to_month' then ojl.credit_application || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        ELSE ojl.credit_application || ' ' || to_char(am.date, 'MM') || pt.name || '月分/' || seo.name
                        END
                        as summery1
                    ,ojl.materials_grouping	
                from								
                    account_move_line aml /* 仕訳項目 */
                    left join								                        					
                    account_move am /* 仕訳 */									
                    on am.id = aml.move_id								
                    inner join								
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
                    and (ojl.debit_sub_account is Null and aml.x_sub_account_id is Null OR ojl.debit_sub_account = any(string_to_array(amc.debit_sub_account, ',')::int[]))					
                    and (ojl.credit_sub_account is Null and aml.x_sub_account_id is Null OR ojl.credit_sub_account = any(string_to_array(amc.credit_sub_account, ',')::int[]))	
                    
                    left join account_account cre_ojl 
                    on ojl.credit_account = cre_ojl.id	
                    left join ss_erp_account_subaccount sub_cre_ojl 
                    on ojl.credit_sub_account = sub_cre_ojl.id						
                where								
                aml.account_id = ojl.debit_account								
                and (pt.categ_id is Null or pt.categ_id = any(string_to_array(ojl.categ_product_id_char, ',')::int[]) )  
                and (pt.id is Null or pt.id = any(string_to_array(ojl.sanhot_product_id_char, ',')::int[]))								
                and aml.debit <> 0  /* 借方を取得 */								
                and aml.parent_state = 'posted'  /* 記帳済み */
                and aml.product_id is not Null
                and ojl.debit_tax_calculation = True							
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
                        when ojl.debit_account_employee_category = 'customer' then '1'				
                        when ojl.debit_account_employee_category = 'vendor' then '2'				
                        else '3'							
                        end as partner_employee_division										
                        , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                            ElSE '' END as partner_employee_code					
                        , seo.organization_code as organization_code								
                        , serd.code as department_code
                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 								
                        sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) :: BIGINT as journal_amount		
                        
                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                        sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) :: BIGINT as tax_excluded_amount								
                        , 0 as tax_amount								
                        , '000' as tax_id								
                        , '0' as tax_entry_division									
                        , pt.name as product
                        , case when ojl.debit_application_edit_indicator = 'month' then ojl.debit_application || ' ' || to_char(am.date, 'MM') || '月分'
                        when ojl.debit_application_edit_indicator = 'month_and_branch' then ojl.debit_application || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        when ojl.debit_application_edit_indicator = 'org_from_to_month' then ojl.debit_application || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        ELSE ojl.debit_application || ' ' || to_char(am.date, 'MM') || pt.name || '月分/' || seo.name
                        END
                        as summery1	
                        ,ojl.materials_grouping		
                        
                    from								
                        account_move_line aml /* 仕訳項目 */
                        left join								                        					
                        account_move am /* 仕訳 */									
                        on am.id = aml.move_id								
                        inner join								
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
                        and (ojl.debit_sub_account is Null and aml.x_sub_account_id is Null OR ojl.debit_sub_account = any(string_to_array(amc.debit_sub_account, ',')::int[]))					
                        and (ojl.credit_sub_account is Null and aml.x_sub_account_id is Null OR ojl.credit_sub_account = any(string_to_array(amc.credit_sub_account, ',')::int[]))		

                        left join account_account de_ojl 
                        on ojl.debit_account = de_ojl.id	
                        left join ss_erp_account_subaccount sub_de_ojl 
                        on ojl.debit_sub_account = sub_de_ojl.id						
                    where								
                    aml.account_id = ojl.credit_account								
                    and (pt.categ_id is Null or pt.categ_id = any(string_to_array(ojl.categ_product_id_char, ',')::int[]) )  
                    and (pt.id is Null or pt.id = any(string_to_array(ojl.sanhot_product_id_char, ',')::int[]))										
                    and aml.credit <> 0  /* 借方を取得 */								
                    and aml.parent_state = 'posted'  /* 記帳済み */
                    and aml.product_id is not Null		
                    and ojl.credit_tax_calculation = True					
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
                    when ojl.credit_account_employee_category = 'customer' then '1'				
                    when ojl.credit_account_employee_category = 'vendor' then '2'				
                    else '3'							
                    end as partner_employee_division										
                    , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                        ElSE '' END as partner_employee_code								
                    , seo.organization_code as organization_code								
                    , serd.code as department_code								
                    , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                    sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                    ELSE sum(aml.price_total) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) :: BIGINT as journal_amount		
                    
                    , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                    sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                    ELSE sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) :: BIGINT as tax_excluded_amount								
                    , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                    sum(aml.price_total - aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                    ELSE sum(aml.price_total - aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) as tax_amount									
                    , aml_atr.account_tax_id as tax_id								
                    , '2' as tax_entry_division								
                    , pt.name as product	
                    , case when ojl.credit_application_edit_indicator = 'month' then ojl.credit_application || ' ' || to_char(am.date, 'MM') || '月分'
                    when ojl.credit_application_edit_indicator = 'month_and_branch' then ojl.credit_application || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                    when ojl.credit_application_edit_indicator = 'org_from_to_month' then ojl.credit_application || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                    ELSE ojl.credit_application || ' ' || to_char(am.date, 'MM') || pt.name || '月分/' || seo.name
                    END
                    as summery1
                    ,ojl.materials_grouping					
                from								
                    account_move_line aml /* 仕訳項目 */
                    left join								                        					
                    account_move am /* 仕訳 */									
                    on am.id = aml.move_id								
                    inner join								
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
                    and (ojl.debit_sub_account is Null and aml.x_sub_account_id is Null OR ojl.debit_sub_account = any(string_to_array(amc.debit_sub_account, ',')::int[]))					
                    and (ojl.credit_sub_account is Null and aml.x_sub_account_id is Null OR ojl.credit_sub_account = any(string_to_array(amc.credit_sub_account, ',')::int[]))								
                where								
                aml.account_id = ojl.credit_account								
                and (pt.categ_id is Null or pt.categ_id = any(string_to_array(ojl.categ_product_id_char, ',')::int[]) )  
                and (pt.id is Null or pt.id = any(string_to_array(ojl.sanhot_product_id_char, ',')::int[]))									
                and aml.credit <> 0  /* 借方を取得 */								
                and aml.parent_state = 'posted'  /* 記帳済み */	
                and aml.product_id is not Null							
                and aml.is_super_stream_linked = False  /* SuperStream未連携 */								
                and am.date BETWEEN '{start_period}' and '{end_period}'		
                and ojl.credit_tax_calculation = True																		                
                --end pattern2

      
                ) result								
                order by
                    move_line_id asc	
                    , line_number asc  								                    						
                    , product asc								
                    , organization_code asc								
                    , department_code asc								
                    , tax_id asc  								
                    , deb_cre_division asc								
            )pattern123								

        """
        self._cr.execute(_select_data)
        data_pattern12 = self._cr.dictfetchall()
        return data_pattern12

    def query_pattern3_debit(self, param):

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
                , journal_amount :: BIGINT								
                , tax_excluded_amount :: BIGINT							
                , tax_amount :: BIGINT								
                , tax_id								
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
                --START PATTERN3 NO DEBIT - NO CREDIT
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
                        when ojl.debit_account_employee_category = 'customer' then '1'				
                        when ojl.debit_account_employee_category = 'vendor' then '2'				
                        else '3'							
                        end as partner_employee_division								
                        , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                        ElSE '' END as partner_employee_code									
                        , seo.organization_code as organization_code								
                        , serd.code as department_code								
                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                        sum(aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) :: BIGINT as journal_amount		

                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                        sum(aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) :: BIGINT as tax_excluded_amount							
                        , 0 as tax_amount
                        , '000' as tax_id								
                        , '0' as tax_entry_division							
                        , pt.name as product	
                        , case when ojl.debit_application_edit_indicator = 'month' then ojl.debit_application || ' ' || to_char(am.date, 'MM') || '月分'
                        when ojl.debit_application_edit_indicator = 'month_and_branch' then ojl.debit_application || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        when ojl.debit_application_edit_indicator = 'org_from_to_month' then ojl.debit_application || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        ELSE ojl.debit_application || ' ' || to_char(am.date, 'MM') || pt.name || '月分/' || seo.name
                        END
                        as summery1	
                        ,ojl.materials_grouping									
                    from	
                        account_move_line aml /* 仕訳項目 */
                        left join account_move am /* 仕訳 */								                        								
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
                        left join account_account cre_ojl 
                        on ojl.credit_account = cre_ojl.id	
                        left join ss_erp_account_subaccount sub_cre_ojl 
                        on ojl.credit_sub_account = sub_cre_ojl.id			                        								
                    where								
                    aml.account_id = ojl.debit_account								
                    and (pt.categ_id is Null or pt.categ_id = any(string_to_array(ojl.categ_product_id_char, ',')::int[]) )  
                    and (pt.id is Null or pt.id = any(string_to_array(ojl.sanhot_product_id_char, ',')::int[]))								
                    and aml.debit <> 0  /* 借方を取得 */		
                    and aml_atr.account_tax_id is Null						
                    and aml.parent_state = 'posted'  /* 記帳済み */
                    and aml.is_super_stream_linked = False  /* SuperStream未連携 */								
                    and ojl.debit_tax_calculation = False								
                    and am.date BETWEEN '{start_period}' and '{end_period}'	                    	

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
                        , '2' as line_number 								
                        , '1' as deb_cre_division								
                        , cre_ojl.code as account_code								
                        , COALESCE(sub_cre_ojl.code, '') as sub_account_code								
                        ,  case when ojl.debit_department_edit_classification = 'no_edits' then serd.code || right(seo.organization_code, 3)
                        when ojl.debit_department_edit_classification = 'first_two_digits' then ojl.debit_accounting_department_code || right(seo.organization_code, 3)				
                        else ojl.debit_accounting_department_code								
                        end as depar_orga_code									
                        ,  case when ojl.debit_account_employee_category = 'no_used' then '0'
                        when ojl.debit_account_employee_category = 'customer' then '1'				
                        when ojl.debit_account_employee_category = 'vendor' then '2'				
                        else '3'							
                        end as partner_employee_division								
                        , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                        ElSE '' END as partner_employee_code									
                        , seo.organization_code as organization_code								
                        , serd.code as department_code								
                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                        sum(aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) :: BIGINT as journal_amount		

                        , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                        sum(aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                        ELSE sum(aml.debit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) :: BIGINT as tax_excluded_amount							
                        , 0 as tax_amount
                        , '000' as tax_id								
                        , '0' as tax_entry_division							
                        , pt.name as product	
                        , case when ojl.credit_application_edit_indicator = 'month' then ojl.credit_application || ' ' || to_char(am.date, 'MM') || '月分'
                        when ojl.credit_application_edit_indicator = 'month_and_branch' then ojl.credit_application || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        when ojl.credit_application_edit_indicator = 'org_from_to_month' then ojl.credit_application || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                        ELSE ojl.credit_application || ' ' || to_char(am.date, 'MM') || pt.name || '月分/' || seo.name
                        END
                        as summery1	
                        ,ojl.materials_grouping									
                    from								
                        account_move_line aml /* 仕訳項目 */
                        left join account_move am /* 仕訳 */								
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
                        left join account_account cre_ojl 
                        on ojl.credit_account = cre_ojl.id	
                        left join ss_erp_account_subaccount sub_cre_ojl 
                        on ojl.credit_sub_account = sub_cre_ojl.id			                        								
                    where								
                    aml.account_id = ojl.debit_account								
                    and (pt.categ_id is Null or pt.categ_id = any(string_to_array(ojl.categ_product_id_char, ',')::int[]) )  
                    and (pt.id is Null or pt.id = any(string_to_array(ojl.sanhot_product_id_char, ',')::int[]))								
                    and aml.debit <> 0  /* 借方を取得 */		
                    and aml_atr.account_tax_id is Null			
                    and ojl.debit_tax_calculation = False			
                    and aml.parent_state = 'posted'  /* 記帳済み */								
                    and aml.is_super_stream_linked = False  /* SuperStream未連携 */								
                    and am.date BETWEEN '{start_period}' and '{end_period}'																									
                --end pattern3											
                ) result								
                order by	
                    move_line_id asc	
                    , line_number asc  								                    					
                    , product asc								
                    , organization_code asc								
                    , department_code asc								
                    , tax_id asc  								
                    , deb_cre_division asc								
            )pattern123								

        """
        self._cr.execute(_select_data)
        data_pattern3 = self._cr.dictfetchall()
        return data_pattern3

    def query_pattern3_credit(self, param):

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
                , journal_amount :: BIGINT								
                , tax_excluded_amount :: BIGINT							
                , tax_amount :: BIGINT								
                , tax_id								
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
                --START PATTERN3 NO DEBIT - NO CREDIT  
                /* 消費税のある商品売上とその消費税を取得する（貸方-税計算なし） */								
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
                    ,  case when ojl.credit_department_editing_classification = 'no_edits' then serd.code || right(seo.organization_code, 3)
                    when ojl.credit_department_editing_classification = 'first_two_digits' then ojl.credit_accounting_department_code || right(seo.organization_code, 3)				
                    else ojl.credit_accounting_department_code								
                    end as depar_orga_code									
                    ,  case when ojl.credit_account_employee_category = 'no_used' then '0'
                    when ojl.credit_account_employee_category = 'customer' then '1'				
                    when ojl.credit_account_employee_category = 'vendor' then '2'				
                    else '3'							
                    end as partner_employee_division									
                    , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                    ElSE '' END as partner_employee_code								
                    , seo.organization_code as organization_code								
                    , serd.code as department_code								
                    , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                    sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                    ELSE sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) :: BIGINT as journal_amount		

                    , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                    sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                    ELSE sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) :: BIGINT as tax_excluded_amount								
                    , 0 as tax_amount								
                    , '000' as tax_id								
                    , '0' as tax_entry_division								
                    , pt.name as product
                    , case when ojl.debit_application_edit_indicator = 'month' then ojl.debit_application || ' ' || to_char(am.date, 'MM') || '月分'
                    when ojl.debit_application_edit_indicator = 'month_and_branch' then ojl.debit_application || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                    when ojl.debit_application_edit_indicator = 'org_from_to_month' then ojl.debit_application || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                    ELSE ojl.debit_application || ' ' || to_char(am.date, 'MM') || pt.name || '月分/' || seo.name
                    END
                    as summery1	
                    ,ojl.materials_grouping								
                from								
                    account_move_line aml /* 仕訳項目 */
                    left join account_move am /* 仕訳 */								
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
                where								
                aml.account_id = ojl.credit_account								
                and (pt.categ_id is Null or pt.categ_id = any(string_to_array(ojl.categ_product_id_char, ',')::int[]) )  
                and (pt.id is Null or pt.id = any(string_to_array(ojl.sanhot_product_id_char, ',')::int[]))									
                and aml.credit <> 0  /* 借方を取得 */
                and aml_atr.account_tax_id is Null								
                and aml.parent_state = 'posted'  /* 記帳済み */								
                and aml.is_super_stream_linked = False  /* SuperStream未連携 */								
                and am.date BETWEEN '{start_period}' and '{end_period}'

                union all								

                /* 消費税のある商品売上とその消費税を取得する（貸方-税計算なし） */								
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
                    when ojl.credit_account_employee_category = 'customer' then '1'				
                    when ojl.credit_account_employee_category = 'vendor' then '2'				
                    else '3'							
                    end as partner_employee_division									
                    , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                    ElSE '' END as partner_employee_code								
                    , seo.organization_code as organization_code								
                    , serd.code as department_code								
                    , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                    sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                    ELSE sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) :: BIGINT as journal_amount		

                    , (CASE WHEN ojl.materials_grouping = TRUE THEN 
                    sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code, aml.product_id)
                    ELSE sum(aml.credit) OVER (PARTITION BY am.date,aml_atr.account_tax_id,aa.code,seas.code,aml.product_id,seo.organization_code, serd.code) END) :: BIGINT as tax_excluded_amount								
                    , 0 as tax_amount								
                    , '000' as tax_id								
                    , '0' as tax_entry_division								
                    , pt.name as product
                    , case when ojl.credit_application_edit_indicator = 'month' then ojl.credit_application || ' ' || to_char(am.date, 'MM') || '月分'
                    when ojl.credit_application_edit_indicator = 'month_and_branch' then ojl.credit_application || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                    when ojl.credit_application_edit_indicator = 'org_from_to_month' then ojl.credit_application || ' ' || to_char(am.date, 'MM') || '月分/' || seo.name 
                    ELSE ojl.credit_application || ' ' || to_char(am.date, 'MM') || pt.name || '月分/' || seo.name
                    END
                    as summery1	
                    ,ojl.materials_grouping								
                from								
                    account_move_line aml /* 仕訳項目 */
                    left join account_move am /* 仕訳 */								
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
                where								
                aml.account_id = ojl.credit_account								
                and (pt.categ_id is Null or pt.categ_id = any(string_to_array(ojl.categ_product_id_char, ',')::int[]) )  
                and (pt.id is Null or pt.id = any(string_to_array(ojl.sanhot_product_id_char, ',')::int[]))									
                and aml.credit <> 0  /* 借方を取得 */
                and aml_atr.account_tax_id is Null								
                and aml.parent_state = 'posted'  /* 記帳済み */								
                and aml.is_super_stream_linked = False  /* SuperStream未連携 */								
                and am.date BETWEEN '{start_period}' and '{end_period}'													
                --end pattern3											
                ) result								
                order by
                    move_line_id asc
                    , line_number asc  								                    	
                    , deb_cre_division asc								
                    ,product asc								
                    , organization_code asc								
                    , department_code asc								
                    , tax_id asc  								
            )pattern123								

        """
        self._cr.execute(_select_data)
        data_pattern3 = self._cr.dictfetchall()
        return data_pattern3

    # transfer between branch
    def query_pattern5(self, param):

        start_period = datetime.combine(self.first_day_period, datetime.min.time())
        end_period = datetime.combine(self.last_day_period, datetime.max.time())

        _select_data = f"""
        WITH odoo_journal_linkage AS (
            SELECT * FROM ss_erp_superstream_linkage_journal where journal_creation = 'transfer_between_base'								
            ),
        part5_categ AS (
        SELECT * FROM (VALUES('merchandise', '{param['product_ctg_merchandise']}':: INT),
            ('product', '{param['product_ctg_product']}':: INT),
            ('stock', '{param['product_ctg_stock']}':: INT)) AS t (categ_key,categ_id)
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
                    , journal_amount :: BIGINT							
                    , tax_excluded_amount :: BIGINT							
                    , tax_amount :: BIGINT			
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
                        when ojl.debit_account_employee_category = 'customer' then '1'				
                        when ojl.debit_account_employee_category = 'vendor' then '2'				
                        else '3'							
                        end as partner_employee_division			
                        , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                        ElSE '' END as partner_employee_code	
                        ,seo.organization_code as organization_code	
                        , serd.code as department_code
                        ,sum(iol.product_uom_qty * prop.value_float) OVER (PARTITION BY sp.date,seo.organization_code, serd.code) :: BIGINT as journal_amount		
                        ,sum(iol.product_uom_qty * prop.value_float) OVER (PARTITION BY sp.date,seo.organization_code, serd.code) :: BIGINT as tax_excluded_amount	
                        , 0 as tax_amount						
                        , '000' as tax_id						
                        , '0' as tax_entry_division	
                        , case when ojl.debit_application_edit_indicator = 'month' then ojl.debit_application || ' ' || to_char(sp.date, 'MM') || '月分'
                            when ojl.debit_application_edit_indicator = 'month_and_branch' then ojl.debit_application || ' ' || to_char(sp.date, 'MM') || '月分/' || seo.name 
                            when ojl.debit_application_edit_indicator = 'org_from_to_month' then ojl.debit_application || '/' || source_seo.name || '->' || dest_seo.name || to_char(sp.date, 'MM') || '月分'
                            when ojl.debit_application_edit_indicator = 'dept_from_to_month' then ojl.debit_application || '/' || source_seo.name || '->' || dest_seo.name || to_char(sp.date, 'MM') || '月分'
                            ELSE ojl.debit_application || ' ' || to_char(sp.date, 'MM') || pt.name || '月分/' || seo.name
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
                        on sp.x_organization_id = any(string_to_array(ojl.credit_related_org_id_char, ',')::int[])
                        and sp.x_organization_dest_id = any(string_to_array(ojl.debit_related_org_id_char, ',')::int[])
                        left join account_account de_ojl 
                        on ojl.debit_account = de_ojl.id	
                        left join ss_erp_account_subaccount sub_de_ojl 
                        on ojl.debit_sub_account = sub_de_ojl.id
                        
                        left join ss_erp_organization source_seo
                        on ojl.credit_related_organization = source_seo.id
                        left join ss_erp_organization dest_seo
                        on ojl.debit_related_organization = dest_seo.id
                        
                        left join part5_categ p5ct
                        on p5ct.categ_key = ojl.product_ctg
                        
                        left join stock_picking_type spt 
                        on sp.picking_type_id = spt.id

                    where						
                    sp.state = 'done'  /* 完了を指定 */						
                    and sp.date BETWEEN '{start_period}' and '{end_period}'					
                    and sp.x_organization_id = any(string_to_array(ojl.credit_related_org_id_char, ',')::int[])  /* 移動元組織（貸方関連組織を指定） */						
                    and sp.x_organization_dest_id = any(string_to_array(ojl.debit_related_org_id_char, ',')::int[]) /* 移動先組織（借方関連組織を指定） */	
                    and io.is_super_stream_linked = False																			
                    and p5ct.categ_id :: INT = pt.categ_id
                    and spt.code = 'incoming'																			
                                                                                                         
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
                    , '2' as line_number 								
                    , '1' as deb_cre_division	
                    , cre_ojl.code as account_code								
                    , COALESCE(sub_cre_ojl.code, '') as sub_account_code	
                    ,  case when ojl.credit_department_editing_classification = 'no_edits' then serd.code || right(seo.organization_code, 3)
                    when ojl.credit_department_editing_classification = 'first_two_digits' then ojl.credit_accounting_department_code || right(seo.organization_code, 3)				
                    else ojl.credit_accounting_department_code								
                    end as depar_orga_code	
                    ,  case when ojl.credit_account_employee_category = 'no_used' then '0'
                    when ojl.credit_account_employee_category = 'customer' then '1'				
                    when ojl.credit_account_employee_category = 'vendor' then '2'				
                    else '3'							
                    end as partner_employee_division			
                    , case when ojl.debit_account_employee_category != 'no_used' then rpad(right(seo.organization_code, 3), 13, '0')
                    ElSE '' END as partner_employee_code	
                    ,seo.organization_code as organization_code	
                    , serd.code as department_code
                    ,sum(iol.product_uom_qty * prop.value_float) OVER (PARTITION BY sp.date,seo.organization_code, serd.code) :: BIGINT as journal_amount		
                    ,sum(iol.product_uom_qty * prop.value_float) OVER (PARTITION BY sp.date,seo.organization_code, serd.code) :: BIGINT as tax_excluded_amount	
                    , 0 as tax_amount						
                    , '000' as tax_id						
                    , '0' as tax_entry_division	
                    , case when ojl.credit_application_edit_indicator = 'month' then ojl.debit_application || ' ' || to_char(sp.date, 'MM') || '月分'
                        when ojl.credit_application_edit_indicator = 'month_and_branch' then ojl.debit_application || ' ' || to_char(sp.date, 'MM') || '月分/' || seo.name 
                        when ojl.credit_application_edit_indicator = 'org_from_to_month' then ojl.debit_application || '/' || source_seo.name || '->' || dest_seo.name || to_char(sp.date, 'MM') || '月分'
                        when ojl.credit_application_edit_indicator = 'dept_from_to_month' then ojl.debit_application || '/' || source_seo.name || '->' || dest_seo.name || to_char(sp.date, 'MM') || '月分'
                        ELSE ojl.credit_application || ' ' || to_char(sp.date, 'MM') || pt.name || '月分/' || seo.name
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
                    on sp.x_organization_id = any(string_to_array(ojl.credit_related_org_id_char, ',')::int[]) 
                    and sp.x_organization_dest_id = any(string_to_array(ojl.debit_related_org_id_char, ',')::int[])		
                    left join account_account cre_ojl 
                    on ojl.credit_account = cre_ojl.id	
                    left join ss_erp_account_subaccount sub_cre_ojl 
                    on ojl.credit_sub_account = sub_cre_ojl.id	
                    
                    left join ss_erp_organization source_seo
                    on ojl.credit_related_organization = source_seo.id
                    left join ss_erp_organization dest_seo
                    on ojl.debit_related_organization = dest_seo.id
                    
                    left join part5_categ p5ct
                    on p5ct.categ_key = ojl.product_ctg	
                    
                    left join stock_picking_type spt 
                    on sp.picking_type_id = spt.id
                    		
                where						
                sp.state = 'done'  /* 完了を指定 */						
                and sp.date BETWEEN '{start_period}' and '{end_period}'							
                and sp.x_organization_id = any(string_to_array(ojl.credit_related_org_id_char, ',')::int[])  /* 移動元組織（貸方関連組織を指定） */						
                and sp.x_organization_dest_id = any(string_to_array(ojl.debit_related_org_id_char, ',')::int[]) /* 移動先組織（借方関連組織を指定） */	
                and io.is_super_stream_linked = False	
                and p5ct.categ_id :: INT = pt.categ_id
                and spt.code = 'outgoing'
            ) result				
                order by
                inventory_order_line_id
                , line_number asc	                
                , deb_cre_division asc						
                , department_code asc
                )pattern5										
"""
        self._cr.execute(_select_data)
        data_pattern5 = self._cr.dictfetchall()
        return data_pattern5

    def _update_account_move_line(self, update_move_line=None):
        if update_move_line:
            update_move_line_str = '(' + ','.join([str(move_line_id) for move_line_id in update_move_line]) + ')'
            query = f"""
                update account_move_line set is_super_stream_linked = True where id in {update_move_line_str}
            """
            self._cr.execute(query)

    def _update_move_between_base(self, update_inventory_order_line=None):
        if update_inventory_order_line:
            update_inventory_order_line_str = '(' + ','.join(
                [str(order_line) for order_line in update_inventory_order_line]) + ')'
            query = f"""
                update ss_erp_inventory_order set is_super_stream_linked = True 
                where id in (select order_id from ss_erp_inventory_order_line where id in {update_inventory_order_line_str})                
            """
            self._cr.execute(query)

    def export_sstream_journal_entry(self):
        # Captured data start record
        file_data = "0,1" + '\r\n'

        param = self.get_a007_param()

        pattern12_data = self.query_pattern12(param)
        pattern3_data_debit = self.query_pattern3_debit(param)
        pattern3_data_credit = self.query_pattern3_credit(param)
        #
        pattern5_data = self.query_pattern5(param)

        # all_pattern_data = pattern3_data
        all_pattern_data = pattern12_data + pattern3_data_debit + pattern5_data

        if not all_pattern_data:
            raise UserError('データがないとか、すべてエクスポートされました。もう一度確認してください。')

        tax_dict = {}
        tax_convert_ids = self.env['ss_erp.code.convert'].search([]).filtered(
            lambda x: x.external_system.code == 'super_stream')
        for tax in tax_convert_ids:
            tax_dict[tax.internal_code.id] = tax.external_code

        update_move_line = []

        for data in pattern3_data_credit:
            if data.get('move_line_id'):
                update_move_line.append(data['move_line_id'])

        list_group = []

        update_inventory_order_line = []
        for index, all_data in enumerate(all_pattern_data):
            if all_data.get('move_line_id'):
                update_move_line.append(all_data['move_line_id'])
            if all_data.get('inventory_order_line_id'):
                update_inventory_order_line.append(all_data['inventory_order_line_id'])
            if index % 2 == 1:
                continue

            if all_data['materials_grouping']:
                if (all_data['slip_date'], all_data['depar_orga_code'], all_data['account_code'],
                                  all_data['sub_account_code'], all_data['product_id']) in list_group:
                    continue
                else:
                    list_group.append((all_data['slip_date'], all_data['depar_orga_code'], all_data['account_code'],
                                  all_data['sub_account_code'], all_data['product_id']))
            else:
                if (all_data['slip_date'], all_data['depar_orga_code'], all_data['account_code'],
                                  all_data['sub_account_code'], all_data['product_id']) in list_group:
                    continue
                else:
                    list_group.append((all_data['slip_date'], all_data['depar_orga_code'], all_data['account_code'],
                                  all_data['sub_account_code'], all_data['product_id']))

            # Document data header record
            doc_header = "1" + '\r\n'
            file_data += doc_header

            # journal entry header region
            journal_header = "2," + param['sstream_company_code'] + "," + param['sstream_slip_group'] + ",," + all_data[
                'slip_date'] + ',,0,1,,,,,0,0,,,,,,,,,,,,,' + '\r\n'
            file_data += journal_header

            if all_data['tax_id'] != '000':
                if all_data['tax_id'] == 0:
                    all_data['tax_id'] = ''
                else:
                    all_data['tax_id'] = tax_dict[all_data['tax_id']] if tax_dict.get(all_data['tax_id']) else ''
            clean_dict_data = deepcopy(all_data)
            if 'move_line_id' in clean_dict_data.keys():
                clean_dict_data.pop('move_line_id')
            if 'materials_grouping' in clean_dict_data.keys():
                clean_dict_data.pop('materials_grouping')
            if 'product_id' in clean_dict_data.keys():
                clean_dict_data.pop('product_id')
            if 'inventory_order_line_id' in clean_dict_data.keys():
                clean_dict_data.pop('inventory_order_line_id')
            debit_line = ','.join(map(str, clean_dict_data.values())) + '\r\n'

            cre_line = all_pattern_data[index + 1]

            if cre_line['tax_id'] != '000':
                if cre_line['tax_id'] == 0:
                    cre_line['tax_id'] = ''
                else:
                    cre_line['tax_id'] = tax_dict[cre_line['tax_id']] if tax_dict.get(cre_line['tax_id']) else ''

            clean_dict_data = deepcopy(cre_line)
            if 'move_line_id' in clean_dict_data.keys():
                clean_dict_data.pop('move_line_id')
            if 'materials_grouping' in clean_dict_data.keys():
                clean_dict_data.pop('materials_grouping')
            if 'product_id' in clean_dict_data.keys():
                clean_dict_data.pop('product_id')
            if 'inventory_order_line_id' in clean_dict_data.keys():
                clean_dict_data.pop('inventory_order_line_id')
            credit_line = ','.join(map(str, clean_dict_data.values())) + '\r\n'

            file_data += debit_line
            file_data += credit_line
            # slip data trailer record
            slip_trailer = "8" + '\r\n'
            file_data += slip_trailer

        self._update_account_move_line(list(set(update_move_line)))
        self._update_move_between_base(list(set(update_inventory_order_line)))

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
