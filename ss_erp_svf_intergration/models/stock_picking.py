# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import base64


def get_multi_character(n, key=' '):
    return key * n


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def delivery_order_svf_template_export(self):
        data_file = [
            '"delivery_slip_number","zip","state_city","address","customer_name","output_date","name","responsible_person","organization_zip","organization_address","organization_phone","organization_fax","product_name","spacification_name","quantity","unit","unit_price","price","rprice_totalemarks","price_total"']
        sale_order_rec = self.sale_id
        for order_line in sale_order_rec.order_line:

            shipping_zip = "〒" + str(
                sale_order_rec.partner_shipping_id.zip) if sale_order_rec.partner_shipping_id.zip else "〒"
            shipping_state_city = str(
                sale_order_rec.partner_shipping_id.state_id.name) if sale_order_rec.partner_shipping_id.state_id.name else "" + str(
                sale_order_rec.partner_shipping_id.city) if sale_order_rec.partner_shipping_id.city else ""
            shipping_address = str(
                sale_order_rec.partner_shipping_id.street) if sale_order_rec.partner_shipping_id.street else "" + str(
                sale_order_rec.partner_shipping_id.street2) if sale_order_rec.partner_shipping_id.street2 else ""
            shipping_name = str(sale_order_rec.partner_shipping_id.name) + ' 様'
            output_date = fields.Datetime.now().strftime("%Y年%m月%d日")
            if sale_order_rec.x_organization_id.responsible_person.user_partner_id.x_responsible_person_printing == 'yes':
                organization_name = sale_order_rec.x_organization_id.name
                responsible_person = sale_order_rec.x_organization_id.responsible_person.name
                organization_zip = sale_order_rec.x_organization_id.organization_zip if sale_order_rec.x_organization_id.organization_zip else ''
                organization_address = sale_order_rec.x_organization_id.organization_state_id.name if sale_order_rec.x_organization_id.organization_state_id.name else '' + sale_order_rec.x_organization_id.organization_city if sale_order_rec.x_organization_id.organization_city else '' + sale_order_rec.x_organization_id.organization_street if sale_order_rec.x_organization_id.organization_street else '' + sale_order_rec.x_organization_id.organization_street2 if sale_order_rec.x_organization_id.organization_street2 else ''
            else:
                organization_name = ''
                responsible_person = ''
                organization_zip = ''
                organization_address = ''

            organization_phone = 'TEL：' + sale_order_rec.x_organization_id.organization_phone if sale_order_rec.x_organization_id.organization_phone else 'TEL：'
            organization_fax = 'FAX：' + sale_order_rec.x_organization_id.organization_fax if sale_order_rec.x_organization_id.organization_fax else 'FAX：'
            data_line = [
                self.name, shipping_zip, shipping_state_city, shipping_address, shipping_name, output_date,
                organization_name, responsible_person, organization_zip, organization_address
                , organization_phone
                , organization_fax
                , order_line.product_id.product_tmpl_id.x_name_abbreviation if order_line.product_id.product_tmpl_id.x_name_abbreviation else ''
                , order_line.product_id.product_tmpl_id.x_name_specification if order_line.product_id.product_tmpl_id.x_name_specification else ''
                , str(order_line.product_uom_qty)
                # hmmmm can't encode unit m3 with shift-jis
                , str(order_line.product_uom.name)
                , str(order_line.price_unit)
                , str(order_line.price_subtotal)
                , str(order_line.x_remarks) if order_line.x_remarks else ''
                , "{:,}".format(int(sale_order_rec.amount_untaxed)) if sale_order_rec.amount_untaxed else ''

            ]

            str_data_line = '","'.join(data_line)
            str_data_line = '"' + str_data_line + '"'
            data_file.append(str_data_line)
        data_send = "\n".join(data_file)

        # b = data_send.encode('utf-8')
        # vals = {
        #     'name': '納品書出力' '.csv',
        #     'datas': base64.b64encode(b).decode('utf-8'),
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

        return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_send, type_report='R009')
