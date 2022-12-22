# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import base64


def get_multi_character(n, key=' '):
    return key * n


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_delivery_amount = fields.Float(compute='_compute_x_delivery_amount')

    def _compute_x_delivery_amount(self):
        for rec in self:
            x_delivery_amount = 0
            for order_line in rec.move_ids_without_package:
                if order_line.sale_line_id:
                    x_delivery_amount += order_line.quantity_done * order_line.sale_line_id.price_unit

            rec.x_delivery_amount = x_delivery_amount

    def delivery_order_svf_template_export(self):
        data_file = [
            '"delivery_slip_number","zip","state_city","address","customer_name","output_date","name","responsible_person","organization_zip","organization_address","organization_phone","organization_fax","product_name","spacification_name","quantity","unit","unit_price","price","rprice_totalemarks","price_total"']
        # sale_order_rec = self.sale_id

        for order_line in self.move_ids_without_package:
            shipping_zip = "〒" + str( self.partner_id.zip) if self.partner_id.zip else "〒"
            shipping_state_city = (str(
                self.partner_id.state_id.name) if self.partner_id.state_id.name else "") + (str(
                self.partner_id.city) if self.partner_id.city else "")
            shipping_address = (str(
                self.partner_id.street) if self.partner_id.street else "") + (str(
                self.partner_id.street2) if self.partner_id.street2 else "")
            shipping_name = str(self.partner_id.name) + ' 様'
            output_date = fields.Datetime.now().strftime("%Y年%m月%d日")
            responsible_person = self.x_organization_id.responsible_person.name if self.partner_id.x_responsible_stamp == 'yes' else ''
            organization_name = self.x_organization_id.name
            organization_zip = "〒" + self.x_organization_id.organization_zip if self.x_organization_id.organization_zip else ''
            organization_address = self.x_organization_id.organization_address if self.x_organization_id.organization_address else ''
            organization_phone = "TEL：" + self.x_organization_id.organization_phone if self.x_organization_id.organization_phone else 'TEL：'
            organization_fax = "FAX：" + self.x_organization_id.organization_fax if self.x_organization_id.organization_fax else 'FAX：'
            price_unit = order_line.sale_line_id.price_unit
            qty = order_line.quantity_done
            price_subtotal = price_unit * qty
            data_line = [
                self.name
                , shipping_zip
                , shipping_state_city
                , shipping_address
                , shipping_name
                , output_date
                , organization_name
                , responsible_person
                , organization_zip
                , organization_address
                , organization_phone
                , organization_fax
                ,
                order_line.product_id.product_tmpl_id.x_name_abbreviation if order_line.product_id.product_tmpl_id.x_name_abbreviation else ''
                ,
                order_line.product_id.product_tmpl_id.x_name_specification if order_line.product_id.product_tmpl_id.x_name_specification else ''
                , f'{qty:.2f}'
                , str(order_line.product_uom.name)
                , "{:,}".format(int(price_unit))
                , "{:,}".format(int(price_subtotal))
                , str(order_line.sale_line_id.x_remarks) if order_line.sale_line_id.x_remarks else ''
                , "￥" + "{:,}".format(int(self.x_delivery_amount)) if self.x_delivery_amount else ''

            ]

            str_data_line = '","'.join(data_line)
            str_data_line = '"' + str_data_line + '"'
            data_file.append(str_data_line)
        data_send = "\n".join(data_file)

        return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_send, type_report='R009')
