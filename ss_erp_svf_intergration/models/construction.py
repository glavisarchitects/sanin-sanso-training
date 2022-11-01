from odoo import fields, models, api
from odoo.exceptions import UserError
import base64
from datetime import datetime


class Construction(models.Model):
    _inherit = 'ss.erp.construction'

    def action_print_estimation(self):
        return self._prepare_data_file()
        # data_file = self._prepare_data_file()
        # if not data_file:
        #     raise UserError("出力対象のデータがありませんでした。")
        # return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_file, type_report='R002')

    def _get_estimation_detail(self):

        fee_product_list = [
            int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_direct_material_cost')),
            int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_direct_labor_cost')),
            int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_direct_outsourcing_cost')),
            int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_direct_expense_cost')),
            int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_indirect_material_cost')),
            int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_indirect_labor_cost')),
            int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_indirect_outsourcing_cost')),
            int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_indirect_expense_cost')),
        ]

        fee_product_list_str = f"({','.join(map(str, fee_product_list))})"

        not_com_list = fee_product_list

        if not self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_legal_welfare_expenses'):
            raise UserError(
                "法定福利費プロダクトの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(ss_erp_construction_legal_welfare_expenses)")
        else:
            ss_erp_construction_legal_welfare_expenses_product = self.env['product.product'].browse(
                int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_legal_welfare_expenses')))
            not_com_list.append(ss_erp_construction_legal_welfare_expenses_product.id)

        if not self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_discount_price'):
            raise UserError(
                "法定福利費プロダクトの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(ss_erp_construction_discount_price)")
        else:
            ss_erp_construction_discount_price_product = self.env['product.product'].browse(
                int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_discount_price')))
            not_com_list.append(ss_erp_construction_discount_price_product.id)

        not_com_list_str = f"({','.join(map(str, not_com_list))})"

        query = f'''
               WITH exp AS (
               SELECT 
                    scc.construction_id,
                    '法定福利費' AS product_name,
                    NULL AS specification,
                    1 AS quantity,
                    '式' AS unit,
                    NULL AS unit_price,
                    scc.subtotal AS amount_of_money,
                    NULL AS subtotal
                FROM ss_erp_construction_component scc
                WHERE scc.product_id = '{ss_erp_construction_legal_welfare_expenses_product.id}' and scc.construction_id = '{self.id}'        
                ),
                fee AS (
                SELECT
                    scc.construction_id,
                    '諸経費' AS product_name,
                    NULL AS specification,
                    1 AS quantity,
                    '式' AS unit,
                    NULL AS unit_price,
                    SUM(scc.subtotal) AS amount_of_money,
                    NULL AS subtotal
                FROM ss_erp_construction_component scc
                WHERE scc.product_id in {fee_product_list_str}
                GROUP BY scc.construction_id
                ),
                dis AS (
                SELECT 
                    scc.construction_id,
                    '値引き' AS product_name,
                    NULL AS specification,
                    1 AS quantity,
                    '式' AS unit,
                    NULL AS unit_price,
                    scc.subtotal AS amount_of_money,
                    NULL AS subtotal
                FROM ss_erp_construction_component scc
                WHERE scc.product_id = '{ss_erp_construction_discount_price_product.id}' and scc.construction_id = '{self.id}'
                ),
                com AS (
                SELECT
                    scc.construction_id,
                    (CASE WHEN scc.product_id is NULL THEN scc.name ELSE pt.name END) as product_name,
                    (CASE WHEN scc.product_id is NULL THEN NULL ELSE pt.x_name_specification END) as specification,
                    (CASE WHEN scc.product_id is NULL THEN NULL ELSE scc.product_uom_qty END) as quantity,
                    (CASE WHEN scc.product_id is NULL THEN NULL ELSE uu.name END) as unit,
                    (CASE WHEN scc.product_id is NULL THEN NULL ELSE scc.sale_price END) as unit_price,
                    (CASE WHEN scc.product_id is NULL THEN NULL ELSE scc.subtotal END) as amount_of_money,
                    sec.amount_total AS subtotal                    
                FROM ss_erp_construction_component scc
                LEFT JOIN ss_erp_construction sec ON sec.id = scc.construction_id
                LEFT JOIN product_product pp ON scc.product_id = pp.id
                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                LEFT JOIN uom_uom uu on scc.product_uom_id = uu.id                
                WHERE (scc.product_id is NULL) or (scc.product_id not in {not_com_list_str}) and scc.construction_id = '{self.id}'
                ),
                detail AS 
                (
                    SELECT * FROM com
                    UNION ALL 
                    SELECT * FROM fee
                    UNION ALL 
                    SELECT * FROM dis
                    UNION ALL 
                    SELECT * FROM exp
                )
                
                SELECT
                rp.NAME AS customer_name,
                sec.name AS department_id,
                to_char( sec.output_date, 'YYYY年MM月DD日' ),
                sec.amount_total AS total,
                concat ( seo.organization_city, seo.organization_street, seo.organization_street2 ) AS address,
                concat ( 'TEL ', seo.organization_phone ) AS tel,
                concat ( 'FAX ', seo.organization_fax ) AS fax,
                concat ( '作成者 ', rp2.NAME ) AS author,
                sec.construction_name,
                '別途協議' AS finish_date,
                tb2.value AS transaction_type,
                to_char( sec.expire_date, 'YYYY年MM月DD日' ) AS date_of_expiry,
                sec.estimation_note AS remarks,
                sec.construction_name AS product_name_head,
                '' AS specification_head,
                1 AS quantity_head,
                '式' AS unit_head,
                '' AS unit_price_head,
                sec.amount_untaxed as amount_of_money_head,
                sec.amount_untaxed as subtotal_head,
                sec.amount_tax as tax_of_money_head,
                sec.amount_total as total_head,
                sec.red_notice as comment_text,
                '' as page_title,
                detail.product_name,
                detail.specification,
                detail.quantity,
                detail.unit,
                detail.unit_price,
                detail.amount_of_money,
                detail.subtotal                
            FROM
                detail 
                LEFT JOIN ss_erp_construction sec ON detail.construction_id = sec.id
                LEFT JOIN res_partner rp ON sec.partner_id = rp.ID 
                LEFT JOIN ss_erp_organization seo ON sec.organization_id = seo.ID 
                LEFT JOIN res_users ru ON sec.printed_user = ru.ID 
                LEFT JOIN res_partner rp2 ON ru.partner_id = rp2.ID 
                LEFT JOIN account_payment_term apt ON sec.payment_term_id = apt.ID
                LEFT JOIN (SELECT * FROM ir_translation where name = 'account.payment.term,name')tb2 on tb2.res_id = apt.id
                WHERE sec.id = '{self.id}'
        '''
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def _prepare_data_file(self):

        fee_product_list = [
            int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_direct_material_cost')),
            int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_direct_labor_cost')),
            int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_direct_outsourcing_cost')),
            int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_direct_expense_cost')),
            int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_indirect_material_cost')),
            int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_indirect_labor_cost')),
            int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_indirect_outsourcing_cost')),
            int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_indirect_expense_cost')),
        ]

        if not self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_legal_welfare_expenses'):
            raise UserError(
                "法定福利費プロダクトの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(ss_erp_construction_legal_welfare_expenses)")
        else:
            ss_erp_construction_legal_welfare_expenses_product = self.env['product.product'].browse(
                int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_legal_welfare_expenses')))

        if not self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_discount_price'):
            raise UserError(
                "法定福利費プロダクトの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(ss_erp_construction_discount_price)")
        else:
            ss_erp_construction_discount_price_product = self.env['product.product'].browse(
                int(self.env['ir.config_parameter'].sudo().get_param('ss_erp_construction_discount_price')))

        # ヘッダ
        new_data = [
            '"customer_name","department_id","output_date","total","address","tel","fax","author",' + \
            '"construction_name","finish_date","transaction_type","date_of_expiry","remarks",' + \
            '"product_name_head","specification_head","quantity_head","unit_head","unit_price_head",' + \
            '"amount_of_money_head","subtotal_head","tax_of_money_head","total_head","comment_text",' + \
            '"page_title","product_name","specification","quantity","unit","unit_price","amount_of_money","subtotal"']

        output_date_str = self.output_date.strftime("%Y年%m月%d日") if self.output_date else datetime.now().strftime(
            "%Y年%m月%d日")
        organization_state_name = self.organization_id.organization_state_id.name or ''
        organization_address = organization_state_name + (
                self.organization_id.organization_city or '') + (
                                       self.organization_id.organization_street or '') + (
                                           self.organization_id.organization_street2 or '')

        organization_phone = "TEL　" + (self.organization_id.organization_phone or '')
        organization_fax = "FAX　" + (self.organization_id.organization_fax or '')
        author = "作成者　" + (self.user_id.partner_id.name or '')
        construction_name = self.construction_name
        transaction_type = self.payment_term_id.name
        date_of_expiry_str = self.expire_date.strftime("%Y年%m月%d日") if self.expire_date else ''

        fee = 0
        discount = 0
        welfare = 0

        for line in self.construction_component_ids:
            if line.product_id and line.product_id.id in fee_product_list:
                fee += line.subtotal
            elif line.product_id and line.product_id.id == ss_erp_construction_discount_price_product.id:
                discount = line.subtotal
            elif line.product_id and line.product_id.id == ss_erp_construction_legal_welfare_expenses_product.id:
                welfare = line.subtotal
            else:
                data_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
                    self.partner_id.display_name,
                    self.name,
                    output_date_str,
                    "{:,}".format(int(self.amount_total)),
                    self.organization_id.display_name,
                    organization_address,
                    organization_phone,
                    organization_fax,
                    author,
                    construction_name,
                    "別途協議",
                    transaction_type if transaction_type else "",
                    date_of_expiry_str if date_of_expiry_str else "",
                    construction_name,
                    "",
                    "1",
                    "式",
                    "",
                    "{:,}".format(int(self.amount_untaxed)),
                    "{:,}".format(int(self.amount_untaxed)),
                    "{:,}".format(int(self.amount_tax)),
                    "{:,}".format(int(self.amount_total)),
                    self.red_notice if self.red_notice else "",
                    "1 " + construction_name,
                    line.product_id.product_tmpl_id.name if line.product_id else line.name,
                    line.product_id.product_tmpl_id.x_name_specification if line.product_id else "",
                    "{:,}".format(int(line.product_uom_qty)) if line.product_id else "",
                    line.product_uom_id.name if line.product_id else "",
                    "{:,}".format(int(line.sale_price)) if line.product_id else "",
                    "{:,}".format(int(line.subtotal)) if line.product_id else "",
                    "")
                new_data.append(data_line)

        if fee != 0:
            data_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
                self.partner_id.display_name,
                self.name,
                output_date_str,
                "{:,}".format(int(self.amount_total)),
                self.organization_id.display_name,
                organization_address,
                organization_phone,
                organization_fax,
                author,
                construction_name,
                "別途協議",
                transaction_type if transaction_type else "",
                date_of_expiry_str if date_of_expiry_str else "",
                construction_name,
                "",
                "1",
                "式",
                "",
                "{:,}".format(int(self.amount_untaxed)),
                "{:,}".format(int(self.amount_untaxed)),
                "{:,}".format(int(self.amount_tax)),
                "{:,}".format(int(self.amount_total)),
                self.red_notice if self.red_notice else "",
                "2 " + construction_name,
                "諸経費",
                "",
                "1",
                "式",
                "",
                "{:,}".format(int(fee)),
                "")
            new_data.append(data_line)

        if discount != 0:
            data_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
                self.partner_id.display_name,
                self.name,
                output_date_str,
                "{:,}".format(int(self.amount_total)),
                self.organization_id.display_name,
                organization_address,
                organization_phone,
                organization_fax,
                author,
                construction_name,
                "別途協議",
                transaction_type if transaction_type else "",
                date_of_expiry_str if date_of_expiry_str else "",
                construction_name,
                "",
                "1",
                "式",
                "",
                "{:,}".format(int(self.amount_untaxed)),
                "{:,}".format(int(self.amount_untaxed)),
                "{:,}".format(int(self.amount_tax)),
                "{:,}".format(int(self.amount_total)),
                self.red_notice if self.red_notice else "",
                "2 " + construction_name,
                "値引き",
                "",
                "1",
                "式",
                "",
                "{:,}".format(int(discount)),
                "")
            new_data.append(data_line)

        if welfare != 0:
            data_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
                self.partner_id.display_name,
                self.name,
                output_date_str,
                "{:,}".format(int(self.amount_total)),
                self.organization_id.display_name,
                organization_address,
                organization_phone,
                organization_fax,
                author,
                construction_name,
                "別途協議",
                transaction_type if transaction_type else "",
                date_of_expiry_str if date_of_expiry_str else "",
                construction_name,
                "",
                "1",
                "式",
                "",
                "{:,}".format(int(self.amount_untaxed)),
                "{:,}".format(int(self.amount_untaxed)),
                "{:,}".format(int(self.amount_tax)),
                "{:,}".format(int(self.amount_total)),
                self.red_notice if self.red_notice else "",
                "2 " + construction_name,
                "法定福利費",
                "",
                "1",
                "式",
                "",
                "{:,}".format(int(welfare)),
                "")
            new_data.append(data_line)

        file_data = "\n".join(new_data)

        b = file_data.encode('shift-jis')
        vals = {
        'name': '工事見積書' '.csv',
        'datas': base64.b64encode(b).decode('shift-jis'),
        'type': 'binary',
        'res_model': 'ir.ui.view',
        'res_id': False,
        }

        file_txt = self.env['ir.attachment'].create(vals)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_txt.id) + '?download=true',
            'target': 'new',
        }
