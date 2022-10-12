from odoo import fields, models, api
from odoo.exceptions import UserError

class Construction(models.Model):
    _inherit = 'ss.erp.construction'

    def action_print_estimation(self):
        data_file = self._prepare_data_file()
        if not data_file:
            raise UserError("出力対象のデータがありませんでした。")
        return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_file, type_report='R002')

    def _get_estimation_detail(self):
        query = f'''
        SELECT
            rp.NAME AS customer_name,
            sec.sequence_number AS department_id,
            to_char( sec.output_date, 'YYYY年MM月DD日' ),
            sec.amount_total AS total,
            concat ( seo.organization_city, seo.organization_street, seo.organization_street2 ) AS address,
            concat ( 'TEL ', seo.organization_phone ) AS tel,
            concat ( 'FAX ', seo.organization_fax ) AS fax,
            concat ( '作成者 ', rp2.NAME ) AS author,
            sec.construction_name,
            '別途協議' AS finish_date,
            apt.NAME AS transaction_type,
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
            '' as product_name,
            '' as specification,
            '' as quantity,
            '' as unit,
            '' as unit_price,
            '' as amount_of_money,
            '' as subtotal
            
        FROM
            ss_erp_construction sec
            LEFT JOIN res_partner rp ON sec.partner_id = rp.
            ID LEFT JOIN ss_erp_organization seo ON sec.organization_id = seo.
            ID LEFT JOIN res_users ru ON sec.printed_user = ru.
            ID LEFT JOIN res_partner rp2 ON ru.partner_id = rp2.
            ID LEFT JOIN account_payment_term apt ON sec.payment_term_id = apt.ID
        WHERE sec.id = '{self.id}'
        '''
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def _prepare_data_file(self):
        # ヘッダ
        new_data = [
            '"customer_name","department_id","output_date","total","address","tel","fax","author",' + \
            '"construction_name","finish_date","transaction_type","date_of_expiry","remarks",' + \
            '"product_name_head","specification_head","quantity_head","unit_head","unit_price_head",' + \
            '"amount_of_money_head","subtotal_head","tax_of_money_head","total_head","comment_text",' + \
            '"page_title","product_name","specification","quantity","unit","unit_price","amount_of_money","subtotal"']
        return False

