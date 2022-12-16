# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import base64
from datetime import datetime
from odoo.exceptions import UserError


def get_multi_character(n, key=' '):
    return key * n


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def estimation_request_svf_template_export(self):
        if self.x_bis_categ_id == 'gas_material':
            type_report = 'R010'
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
            type_report = 'R010_construction'
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
        # b = data_send.encode('shift-jis')
        # vals = {
        #     'name': '見積依頼書' '.csv',
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

    def order_confirm_coo_com_to_ss_svf_template_export(self):
        if self.x_bis_categ_id != 'construction':
            raise UserError(
                'Puchase Order 工事のみが「注文請書」を生成できます')
        data_file = [
            '"output_date","orderer_address","orderer_name","address","tel","fax","author","supplier_code","order_number","construction_number","construction_name","delivery_location","construction_date_start","construction_date_end","order_amount","consumption_tax","without_tax_amount","receipt_method","due date","contract_term_notice","contract_term_notice","head_line_number","head_product_name","head_specification","head_quantity","head_unit","head_unit_price","head_amount_of_money","head_total_money","line_number","product_name","specification","quantity","unit","unit_price","amount_of_money","total_money"']
        num = 1
        for line in self.order_line:
            if not line.product_id:
                continue
            output_date = datetime.now().strftime("%Y年%m月%d日")
            orderer_address = (str(self.x_organization_id.organization_state_id.name) if self.x_organization_id.organization_state_id.name else "") \
                      + (str(self.x_organization_id.organization_city) if self.x_organization_id.organization_city else "") \
                      + (str( self.x_organization_id.organization_street) if self.x_organization_id.organization_street else "") \
                      + (str(self.x_organization_id.organization_street2) if self.x_organization_id.organization_street2 else "")
            orderer_name = self.partner_id.x_purchase_user_id.company_id.name + "　殿" if self.partner_id.x_purchase_user_id.company_id.name else ''
            address = (str(self.partner_id.state_id.name) if self.partner_id.state_id.name else "") \
                              + (str(self.partner_id.city) if self.partner_id.city else "") \
                              + (str(self.partner_id.street) if self.partner_id.street else "") \
                              + (str(self.partner_id.street2) if self.partner_id.street2 else "")

            tel = ""
            fax = ""
            author = self.user_id.name if self.user_id.name else ""
            supplier_code = self.partner_id.ref if self.partner_id.ref else ""
            order_number = self.order_number if self.order_number else ""
            construction_number = self.x_construction_order_id.sequence_number if self.x_construction_order_id.sequence_number else ""
            construction_name = self.name if self.name else ""
            delivery_location = self.delivery_location if self.delivery_location else ""
            construction_date_start = self.x_construction_period_start.strftime("%Y年%m月%d日") if self.x_construction_period_start else ""
            date_planed_finished = self.x_construction_period_end.strftime("%Y年%m月%d日") if self.x_construction_period_end else ""
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
        # b = data_send.encode('shift-jis')
        # vals = {
        #     'name': '注文請書(協力会社→SS)' '.csv',
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
        return self.env['svf.cloud.config'].sudo().svf_template_export_common(data=data_send, type_report='R008_toSS')