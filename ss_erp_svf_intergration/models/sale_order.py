from odoo import models, fields, api, _
import base64
from datetime import datetime


def get_multi_character(n, key=' '):
    return key * n


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # x_due_date = fields.Date(string="見積有効期限")
    x_due_date_time = fields.Integer(string="見積有効期限")
    x_which_due_date = fields.Selection([('time', '期間指定'), ('date', '日付指定')], default='date',
                                        string="見積有効タイプ")

    x_tax_type = fields.Selection([('include', '税込'), ('exclude', '税別')], default='include')

    x_partner_name = fields.Char(string='顧客名', related='partner_id.name')
    x_delivery_address = fields.Char(string='納入場所', related='partner_shipping_id.name')
    x_remark = fields.Char(string='備考')
    x_delivery_note = fields.Char('納期')
    x_delivery_date = fields.Date(string='納期')
    x_payment_term = fields.Char('取引方法')

    def estimation_request_svf_template_export(self):
        data_file = [
            '"doc_number","print_date","custmer_name","branch_manager","branch_address","branch_tel","branch_fax",'
            '"total_amount","dest_address","due_date","payment_term","estimate_expiry_date","note",'
            '"line_number","product_name","specification_name","qty","uom","price_unit","price_subtotal","line_subtotal","line_amount_tax","line_total_amount"']

        rfq_name = self.name
        rfq_issue_date = datetime.now().strftime("%Y年%m月%d日")
        branch_manager = '支店長　' + self.x_organization_id.responsible_person.name if self.x_organization_id.responsible_person else ''
        due_date = self.validity_date.strftime("%Y年%m月%d日") if self.validity_date else ''
        partner_name = self.x_partner_name + '殿'
        delivery_address = self.x_delivery_address
        delivery_note = self.x_delivery_note if self.x_delivery_note else ''
        payment_term = self.payment_term_id.name if self.payment_term_id else ''
        organization_address = self.x_organization_id.organization_address if self.x_organization_id.organization_address else ''
        organization_fax = 'TEL　' + self.x_organization_id.organization_fax if self.x_organization_id.organization_fax else ''
        organization_phone = 'FAX　' + self.x_organization_id.organization_phone if self.x_organization_id.organization_phone else ''
        amount_total = int(self.amount_total) if self.x_tax_type == 'include' else int(self.amount_untaxed)
        amount_total = "￥" + "{:,}".format(amount_total) + "―"
        amount_untaxed = "￥" + "{:,}".format(int(self.amount_untaxed)) if self.x_tax_type == 'include' else ''
        amount_tax = "￥" + "{:,}".format(int(self.amount_tax)) if self.x_tax_type == 'include' else ''
        # footer
        notes = self.x_remark if self.x_remark else ''

        count = 1
        for line in self.order_line:
            if not line.product_id:
                continue

            product_uom_qty = "{:,}".format(int(line.product_uom_qty))
            price_unit = "{:,}".format(int(line.price_unit))
            price_subtotal = "{:,}".format(int(line.price_subtotal))

            data_line = [
                rfq_name
                , rfq_issue_date
                , partner_name
                , branch_manager
                , organization_address
                , organization_phone
                , organization_fax
                , amount_total
                , delivery_address
                , delivery_note
                , payment_term
                , due_date
                , notes
                , str(count)
                ,
                line.product_id.product_tmpl_id.x_name_abbreviation if line.product_id.product_tmpl_id.x_name_abbreviation else line.product_id.product_tmpl_id.name
                ,
                line.product_id.product_tmpl_id.x_name_specification if line.product_id.product_tmpl_id.x_name_specification else ''
                , product_uom_qty
                , line.product_uom.name
                , price_unit
                , price_subtotal
                , amount_untaxed
                , amount_tax
                , amount_total
            ]

            str_data_line = '","'.join(data_line)
            str_data_line = '"' + str_data_line + '"'
            data_file.append(str_data_line)
            count += 1
        data_send = "\n".join(data_file)

        return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_send, type_report='R007')

        # b = data_send.encode('shift-jis')
        # vals = {
        #     'name': '見積書' '.csv',
        #     'datas': base64.b64encode(b).decode('shift-jis'),
        #     'type': 'binary',
        #     'res_model': 'ir.ui.view',
        #     'x_no_need_save': True,
        #     'res_id': False,
        # }
        #
        # file_txt = self.env['ir.attachment'].create(vals)
        #
        # return {
        #     'type': 'ir.actions.act_url',
        #     'url': '/web/content/' + str(file_txt.id) + '?download=true',
        #     'target': 'new',
        # }
