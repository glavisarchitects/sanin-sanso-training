# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import base64


def get_multi_character(n, key=' '):
    return key * n


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def estimation_request_svf_template_export(self):
        if self.x_bis_categ_id == 'gas_material':
            data_file = [
                '"rfq_issue_date","partner_name","partner_text","company_name","organization_name","organization_address","organization_tel","organization_fax","purchase_number","date_planned","date_order","purchase_user_name","dest_address","dropship_text","product_name","product_note","product_qty","product_uom","notes","dest_address_info","url"']
            for line in self.order_line:
                if not line.product_id:
                    continue
                rfq_issue_date = self.x_rfq_issue_date.strftime("%Y年%m月%d日") if self.x_rfq_issue_date else ''
                organization_address = self.x_organization_id.organization_address if self.x_organization_id.organization_address else ''
                organization_fax = self.x_organization_id.organization_fax if self.x_organization_id.organization_fax else ''
                organization_phone = self.x_organization_id.organization_phone if self.x_organization_id.organization_phone else ''
                date_planned = self.date_planned.strftime("%Y年%m月%d日") if self.date_planned else ''
                date_order = self.date_order.strftime("%Y年%m月%d日") if self.date_order else ''

                header_organization_name = self.x_organization_id.name + '入荷'
                purchase_user_name = self.user_id.name if self.user_id.name else ''

                # detail
                product_note = line.name if line.name else ''

                # footer
                notes = self.notes if self.notes else ''
                x_dest_address_info = self.x_dest_address_info if self.x_dest_address_info else ''
                website = self.company_id.website if self.company_id.website else ''
                data_line = [rfq_issue_date, self.partner_id.name, "下記商品の見積を依頼します。",
                             str(self.company_id.name), str(self.x_organization_id.name), organization_address,
                             organization_phone, organization_fax, self.name, date_planned, date_order,
                             purchase_user_name, header_organization_name, "直送は下部の直送先情報参照",
                             line.product_id.name,
                             product_note,
                             str(line.product_qty), line.product_uom.name, notes,
                             x_dest_address_info, website]

                str_data_line = '","'.join(data_line)
                str_data_line = '"' + str_data_line + '"'
                data_file.append(str_data_line)
            data_send = "\n".join(data_file)

        # construction
        else:
            data_file = [
                '"rfq_issue_date","partner_id","partner_id_text","comapany_id","organization_id",'
                '"organization_address","organization_tel","organization_fax","purchase_number","date_planned","date_order",'
                '"purchase_user_name","dest_address","dropship_text","product_id","product_name","product_note","product_qty",'
                '"construction_title","construction_name","construction_spot","construction_info","construction_period_start",'
                '"construction_method","supplies_check","construction_terms","construction_payment_terms","explanation_check",'
                '"notes","dest_address_info","ss_construction_subcontract_title","ss_construction_subcontract","url"']
            for line in self.order_line:
                if not line.product_id:
                    continue
                rfq_issue_date = self.x_rfq_issue_date.strftime("%Y年%m月%d日") if self.x_rfq_issue_date else ''
                organization_address = self.x_organization_id.organization_address if self.x_organization_id.organization_address else ''
                organization_fax = self.x_organization_id.organization_fax if self.x_organization_id.organization_fax else ''
                organization_phone = self.x_organization_id.organization_phone if self.x_organization_id.organization_phone else ''
                date_planned = self.date_planned.strftime("%Y年%m月%d日") if self.date_planned else ''
                date_order = self.date_order.strftime("%Y年%m月%d日") if self.date_order else ''

                header_organization_name = self.x_organization_id.name + '入荷'
                purchase_user_name = self.user_id.name if self.user_id.name else ''

                # detail
                x_name_specification = line.product_id.x_name_specification if line.product_id.x_name_specification else ''
                product_note = line.name if line.name else ''

                # purchase order
                x_construction_name = self.x_construction_name if self.x_construction_name else ''
                construction_period_start = self.x_construction_period_start.strftime(
                    "%Y年%m月%d日") if self.x_construction_period_start else '' + '~' + self.x_construction_period_end.strftime(
                    "%Y年%m月%d日") if self.x_construction_period_end else ''
                x_supplies_info = get_multi_character(3 * 4) + (self.x_supplies_info if self.x_supplies_info else "")
                supplies_check = "あり" + x_supplies_info if self.x_supplies_check == 'exist' else "なし"
                construction_payment_terms = "当社規定による、月末締切・翌月末支払\r\n" + "現金" + get_multi_character(
                    2 * 4) + str(
                    self.x_construction_payment_cash) + "%" + get_multi_character(3 * 4) + "手形" + get_multi_character(
                    3 * 4) + str(self.x_construction_payment_bill) + "%"
                explanation_check = self.x_explanation_check + "\r\n" + self.x_explanation_date.strftime(
                    "%Y年%m月%d日") + self.x_explanation_spot if self.x_explanation_check == 'exist' else self.x_explanation_check

                # footer
                notes = self.notes if self.notes else ''
                construction_spot = self.x_construction_spot if self.x_construction_spot else ''
                x_dest_address_info = self.x_dest_address_info if self.x_dest_address_info else ''
                ss_erp_construction_subcontract = str(
                    self.x_construction_subcontract) if self.x_construction_subcontract else ""

                website = self.company_id.website if self.company_id.website else ''
                data_line = [rfq_issue_date,
                             self.partner_id.name,
                             "下記商品の見積を依頼します。",
                             str(self.company_id.name),
                             str(self.x_organization_id.name),
                             organization_address,
                             organization_phone,
                             organization_fax,
                             self.name,
                             date_planned,
                             date_order,
                             purchase_user_name,
                             header_organization_name,
                             "※直送先は下部の直送先情報を参照",
                             x_name_specification,
                             line.product_id.name,
                             product_note,
                             str(line.product_qty),
                             "工事情報",
                             x_construction_name,
                             construction_spot,
                             "別途設計書による",
                             construction_period_start,
                             supplies_check,
                             "別途設計書、施工計画書による",
                             construction_payment_terms,
                             explanation_check,
                             notes,
                             x_dest_address_info,
                             "下請工事の予定価格と見積期間",
                             ss_erp_construction_subcontract,
                             website]

                str_data_line = '","'.join(data_line)
                str_data_line = '"' + str_data_line + '"'
                data_file.append(str_data_line)
            data_send = "\n".join(data_file)
        b = data_send.encode('shift-jis')
        vals = {
            'name': '見積依頼書' '.csv',
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
        # return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_send, type_report='R010')

    def po_svf_template_export(self):
        if self.x_bis_categ_id == 'gas_material':
            type_report = 'R011_1'
            data_file = [
                '"purchase_order_code","issue_date","company_name","branch_name","branch_address","branch_tel",'+ \
                '"branch_fax","purchase_member","branch_receive","customer_name","customer_tel","customer_fax",'+ \
                '"price_subtotal","amount_tax","amount_total","notes","dest_info","website","page","product_name",'+ \
                '"quantity","unit","price_unit","price_per_product","price_tax","fixed_cost","date_planned"']
            for line in self.order_line:
                if not line.product_id:
                    continue
                x_po_issue_date = self.x_po_issue_date.strftime("%Y年%m月%d日") if self.x_po_issue_date else ''
                date_planned = line.date_planned.strftime("%Y年%m月%d日") if line.date_planned else ''
                organization_address = self.x_organization_id.organization_address if self.x_organization_id.organization_address else ''
                organization_fax = self.x_organization_id.organization_fax if self.x_organization_id.organization_fax else ''
                organization_phone = self.x_organization_id.organization_phone if self.x_organization_id.organization_phone else ''

                purchase_user_name = self.user_id.name if self.user_id.name else ''

                dest_info = self.x_dest_address_info if self.x_dest_address_info else ''

                # footer
                notes = self.notes if self.notes else ''
                website = self.company_id.website if self.company_id.website else ''
                price_tax = ''
                if line.taxes_id:
                    price_tax = str(int(line.taxes_id[0].amount)) + '%'
                data_line = [self.name,
                             x_po_issue_date,
                             self.company_id.name,
                             self.x_organization_id.name,
                             organization_address,
                             organization_phone,
                             organization_fax,
                             purchase_user_name,
                             self.picking_type_id.default_location_dest_id.name,
                             self.partner_id.name,
                             self.partner_id.phone if self.partner_id.phone else '',
                             self.partner_id.x_fax if self.partner_id.x_fax else '',
                             str(int(self.amount_untaxed)),
                             str(int(self.amount_tax)),
                             str(int(self.amount_total)),
                             notes,
                             dest_info,
                             website,
                             '',
                             line.product_id.product_tmpl_id.name,
                             str(line.product_qty),
                             line.product_uom.name,
                             str(int(line.price_unit)),
                             str(int(line.price_subtotal)),
                             price_tax,
                             str(int(line.x_fixed_cost)),
                             date_planned,
                             ]

                str_data_line = '","'.join(data_line)
                str_data_line = '"' + str_data_line + '"'
                data_file.append(str_data_line)
            data_send = "\n".join(data_file)

        # construction
        else:
            type_report = 'R011_2'
            data_file = [
                '"purchase_order_code","issue_date","company_name","branch_name","branch_address",'+ \
                '"branch_tel","branch_fax","purchase_member","branch_receive","message1","customer_name",'+ \
                '"customer_tel","customer_fax","price_subtotal","amount_tax","amount_total","notes","dest_info",'+ \
                '"website","page","construction_info","construction_name","construction_spot","overview",'+ \
                '"conditions","planned_period","supplies_check","supplies_info","explanation_check",'+ \
                '"explanation_date","explanation_spot","payment_list","cash","bill","product_name",'+ \
                '"quantity","unit","price_unit","price_per_product","price_tax","fixed_cost","date_planned"']
            for line in self.order_line:
                if not line.product_id:
                    continue
                x_po_issue_date = self.x_po_issue_date.strftime("%Y年%m月%d日") if self.x_po_issue_date else ''
                x_explanation_date = self.x_explanation_date.strftime("%Y年%m月%d日") if self.x_explanation_date else ''
                organization_address = self.x_organization_id.organization_address if self.x_organization_id.organization_address else ''
                organization_fax = self.x_organization_id.organization_fax if self.x_organization_id.organization_fax else ''
                organization_phone = self.x_organization_id.organization_phone if self.x_organization_id.organization_phone else ''
                date_planned = self.date_planned.strftime("%Y年%m月%d日") if self.date_planned else ''

                purchase_user_name = self.user_id.name if self.user_id.name else ''

                # purchase order
                x_construction_name = self.x_construction_name if self.x_construction_name else ''
                construction_period_start = self.x_construction_period_start.strftime(
                    "%Y年%m月%d日") if self.x_construction_period_start else '' + '~' + self.x_construction_period_end.strftime(
                    "%Y年%m月%d日") if self.x_construction_period_end else ''
                dest_info = self.x_dest_address_info if self.x_dest_address_info else ''

                # footer
                notes = self.notes if self.notes else ''
                construction_spot = self.x_construction_spot if self.x_construction_spot else ''

                website = self.company_id.website if self.company_id.website else ''
                price_tax = ''
                if line.taxes_id:
                    price_tax = str(int(line.taxes_id[0].amount)) + '%'
                data_line = [
                    self.name,
                    x_po_issue_date,
                    str(self.company_id.name),
                    str(self.x_organization_id.name),
                    organization_address,
                    organization_phone,
                    organization_fax,
                    purchase_user_name,
                    self.picking_type_id.default_location_dest_id.name,
                    '※直送は下部の直送先情報参照示',
                    self.partner_id.name,
                    self.partner_id.phone if self.partner_id.phone else '',
                    self.partner_id.x_fax if self.partner_id.x_fax else '',
                    str(int(self.amount_untaxed)),
                    str(int(self.amount_tax)),
                    str(int(self.amount_total)),
                    notes,
                    dest_info,
                    website,
                    '',
                    '工事情報',
                    x_construction_name,
                    construction_spot,
                    '別途設計書による',
                    '別途設計書、施工計画書による',
                    construction_period_start,
                    '有' if self.x_supplies_check == 'exist' else 'なし',
                    self.x_supplies_info if self.x_supplies_info else '',
                    '有' if self.x_explanation_check == 'exist' else 'なし',
                    x_explanation_date,
                    construction_spot,
                    '支払条件(当社規定による、月末締切・翌月末支払)',
                    str(int(self.x_construction_payment_cash)) if self.x_construction_payment_cash != 0 else '',
                    str(int(self.x_construction_payment_bill)) if self.x_construction_payment_bill != 0 else '',
                    line.product_id.product_tmpl_id.name,
                    str(int(line.product_qty)),
                    line.product_uom.name,
                    str(int(line.price_unit)),
                    str(int(line.price_subtotal)),
                    price_tax,
                    str(int(line.x_fixed_cost)),
                    date_planned,
                    ]

                str_data_line = '","'.join(data_line)
                str_data_line = '"' + str_data_line + '"'
                data_file.append(str_data_line)
            data_send = "\n".join(data_file)
        # b = data_send.encode('shift-jis')
        # vals = {
        #     'name': '発注書' '.csv',
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

        return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_send, type_report=type_report)
