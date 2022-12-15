from odoo import fields, models, api
from odoo.exceptions import UserError
import base64
from datetime import datetime


class Construction(models.Model):
    _inherit = 'ss.erp.construction'

    def action_print_estimation(self):
        if self.print_type == 'detail':
            return self._prepare_data_file()
        else:
            return self._prepare_data_file_set()
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
                "値引きプロダクトの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(ss_erp_construction_discount_price)")
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

    def _prepare_data_file_set(self):

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
        remarks = self.estimation_note if self.estimation_note else ''

        data_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
            self.partner_id.display_name,        # customer_name
            self.name,                           # department_id
            output_date_str,                     # output_date
            "{:,}".format(int(self.amount_total)),#total
            organization_address,
            organization_phone,
            organization_fax,
            author,
            construction_name,
            "別途協議",
            transaction_type if transaction_type else "",
            date_of_expiry_str if date_of_expiry_str else "",
            remarks,
            construction_name,
            "",
            "1",
            "式",
            "",
            "{:,}".format(int(self.amount_untaxed)),
            "{:,}".format(int(self.amount_untaxed)),
            "{:,}".format(int(self.amount_tax)),
            "{:,}".format(int(self.amount_total)),
            "",
            "1 " + construction_name,
            "",
            "",
            "",
            "",
            "",
            "",
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
                "値引きプロダクトの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(ss_erp_construction_discount_price)")
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
        remarks = self.estimation_note if self.estimation_note else ''

        fee = 0
        discount = 0
        welfare = 0

        for line in self.construction_component_ids:
            x_name_specification = ""
            if line.product_id:
                if line.product_id.product_tmpl_id.x_name_specification:
                    x_name_specification = line.product_id.product_tmpl_id.x_name_specification

            if line.product_id and line.product_id.id in fee_product_list:
                fee += line.subtotal
            elif line.product_id and line.product_id.id == ss_erp_construction_discount_price_product.id:
                discount = line.subtotal
            elif line.product_id and line.product_id.id == ss_erp_construction_legal_welfare_expenses_product.id:
                welfare = line.subtotal
            else:
                data_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
                    self.partner_id.display_name,        # customer_name
                    self.name,                           # department_id
                    output_date_str,                     # output_date
                    "{:,}".format(int(self.amount_total)),#total
                    organization_address,
                    organization_phone,
                    organization_fax,
                    author,
                    construction_name,
                    "別途協議",
                    transaction_type if transaction_type else "",
                    date_of_expiry_str if date_of_expiry_str else "",
                    remarks,
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
                    x_name_specification,
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
                organization_address,
                organization_phone,
                organization_fax,
                author,
                construction_name,
                "別途協議",
                transaction_type if transaction_type else "",
                date_of_expiry_str if date_of_expiry_str else "",
                remarks,
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
                "{:,}".format(int(self.amount_untaxed)) if (discount == 0 and welfare == 0) else ""
            )
            new_data.append(data_line)

        if discount != 0:
            data_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
                self.partner_id.display_name,
                self.name,
                output_date_str,
                "{:,}".format(int(self.amount_total)),
                organization_address,
                organization_phone,
                organization_fax,
                author,
                construction_name,
                "別途協議",
                transaction_type if transaction_type else "",
                date_of_expiry_str if date_of_expiry_str else "",
                remarks,
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
                "{:,}".format(int(self.amount_untaxed)) if (welfare == 0) else ""
            )
            new_data.append(data_line)

        if welfare != 0:
            data_line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
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
                remarks,
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
                "{:,}".format(int(self.amount_untaxed)))
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

    def order_confirm_svf_template_export(self):
        data_file = [
            '"output_date","orderer_address","orderer_name","address","tel","fax","author","supplier_code","order_number","construction_number","construction_name","delivery_location","construction_date_start","construction_date_end","order_amount","consumption_tax","without_tax_amount","receipt_method","due date","contract_term_notice","contract_term_notice","head_line_number","head_product_name","head_specification","head_quantity","head_unit","head_unit_price","head_amount_of_money","head_total_money","line_number","product_name","specification","quantity","unit","unit_price","amount_of_money","total_money"']
        num = 1
        for line in self.construction_component_ids:
            if not line.product_id:
                continue
            output_date = datetime.now().strftime("%Y年%m月%d日")
            orderer_address = str(
                self.partner_id.state_id.name) if self.partner_id.state_id.name else "" + str(
                self.partner_id.city) if self.partner_id.city else "" + str(
                self.partner_id.street) if self.partner_id.street else "" + str(
                self.partner_id.street2) if self.partner_id.street2 else ""
            orderer_name = self.partner_id.name + "　殿"
            address = str(
                self.organization_id.organization_state_id.name) if self.organization_id.organization_state_id.name else "" + str(
                self.organization_id.organization_city) if self.organization_id.organization_city else "" + str(
                self.organization_id.organization_street) if self.organization_id.organization_street else "" + str(
                self.organization_id.organization_street2) if self.organization_id.organization_street2 else ""

            tel = self.organization_id.organization_phone if self.organization_id.organization_phone else ""
            fax = self.organization_id.organization_fax if self.organization_id.organization_fax else ""
            author = self.user_id.name if self.user_id.name else ""
            supplier_code = self.partner_id.ref if self.partner_id.ref else ""
            order_number = self.order_number if self.order_number else ""
            construction_number = self.sequence_number if self.sequence_number else ""
            construction_name = self.name if self.name else ""
            delivery_location = self.delivery_location if self.delivery_location else ""
            construction_date_start = self.plan_date.strftime("%Y年%m月%d日") if self.plan_date else ""
            date_planed_finished = self.date_planed_finished.strftime("%Y年%m月%d日") if self.date_planed_finished else ""
            order_amount = "{:,}".format(int(self.amount_total)) if self.amount_total else ""
            consumption_tax = "{:,}".format(int(self.amount_tax)) if self.amount_tax else ""
            without_tax_amount = "{:,}".format(int(self.amount_untaxed)) if self.amount_untaxed else ""
            receipt_method = self.receipt_type if self.receipt_type else ""
            due_date = self.payment_term_id.name if self.payment_term_id else ""
            contract_term_notice = ""
            param_term_notice = self.env['ir.config_parameter'].sudo().get_param('r008_contraction_other_term_notice')
            other_term_notice = param_term_notice if param_term_notice else ''
            if self.export_type == 'complete_set':
                # 一式
                head_line_number = '1'
                head_product_name = self.name if self.name else ''
                head_specification = ''
                head_quantity = '1'
                head_unit = '式'
                head_unit_price = ''
                head_amount_of_money = "{:,}".format(int(self.amount_untaxed)) if self.amount_untaxed else ""
                head_total_money = "{:,}".format(int(self.amount_untaxed)) if self.amount_untaxed else ""

                # 　明細
                line_number = ''
                product_name = ''
                specification = ''
                quantity = ''
                unit = ''
                unit_price = ''
                amount_of_money = ''
                total_money = ''
            else:
                head_line_number = ''
                head_product_name = ''
                head_specification = ''
                head_quantity = ''
                head_unit = ''
                head_unit_price = ''
                head_amount_of_money = ""
                head_total_money = ""

                # 　明細
                line_number = str(num)
                product_name = line.product_id.name
                specification = line.product_id.x_name_specification if line.product_id.x_name_specification else ''
                quantity = str(line.product_uom_qty) if line.product_uom_qty else ''
                unit = line.product_uom_id.name if line.product_uom_id.name else ''
                unit_price = str(line.sale_price) if line.sale_price else ''
                amount_of_money = "{:,}".format(int(line.subtotal)) if line.subtotal else ""
                total_money = "{:,}".format(int(self.amount_untaxed)) if self.amount_untaxed else ""

                num += 1

            data_line = [output_date, orderer_address, orderer_name, address, tel, fax, author, supplier_code,
                         order_number, construction_number, construction_name, delivery_location,
                         construction_date_start, date_planed_finished, order_amount, consumption_tax,
                         without_tax_amount, receipt_method, due_date, contract_term_notice, other_term_notice,
                         head_line_number, head_product_name, head_specification, head_quantity, head_unit,
                         head_unit_price, head_amount_of_money, head_total_money, line_number, product_name,
                         specification, quantity, unit, unit_price, amount_of_money, total_money]

            str_data_line = '","'.join(data_line)
            str_data_line = '"' + str_data_line + '"'
            data_file.append(str_data_line)

        data_send = "\n".join(data_file)
        b = data_send.encode('shift-jis')
        vals = {
            'name': '注文請書(SS→発注者)' '.csv',
            'datas': base64.b64encode(b).decode('shift-jis'),
            'type': 'binary',
            'res_model': 'ir.ui.view',
            'x_no_need_save': True,
            'res_id': False,
        }

        file_txt = self.env['ir.attachment'].create(vals)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_txt.id) + '?download=true',
            'target': 'new',
        }
        # return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_send, type_report='R008')
