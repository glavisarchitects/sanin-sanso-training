# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime

class IFDBYGHeader(models.Model):
    _name = 'ss_erp.ifdb.yg.header'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Yamasan Gas Supply Header'

    name = fields.Char(string='名称')
    upload_date = fields.Datetime(
        string='アップロード日時', index=True, required=True,
		default=fields.Datetime.now())
    user_id = fields.Many2one('res.users', string='担当者', tracking=True)
    branch_id = fields.Many2one(
        'ss_erp.organization', string='支店', tracking=True)
    status = fields.Selection([
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり'),
    ], string='ステータス', default='wait', index=True,compute='_compute_status')
    meter_reading_date = fields.Date(string='検針年月', index=True)
    summary_ids = fields.One2many(
        'ss_erp.ifdb.yg.summary', 'header_id', '検針集計表')
    detail_ids = fields.One2many(
        'ss_erp.ifdb.yg.detail', 'header_id', '検針明細表')

    @api.depends('summary_ids.status')
    def _compute_status(self):
        for record in self:
            if record.summary_ids:
                status_list = record.summary_ids.mapped('status')
                record.status = "success"
                if "error" in status_list:
                    record.status = "error"
                elif "wait" in status_list:
                    record.status = "wait"
            else:
                record.status = "wait"

    def btn_processing_execution(self):
        for record in self:
            record._processing_excution()

    def _processing_excution(self):
        self.ensure_one()
        exe_data = self.summary_ids.filtered(lambda line: line.status in ('wait', 'error')).sorted(
            key=lambda k: (k['partner_id']))
        exe_detail_data = self.detail_ids.sorted(key=lambda k: (k['customer_cd']))

        # get customer code convert
        external_partners = list(set(exe_data.mapped('partner_id')))
        yamasan_gas_type_ids = self.env['ss_erp.external.system.type'].search([('code', '=', 'yamasan_gas')])
        cust_code_type_ids = self.env['ss_erp.convert.code.type'].search([('code', '=', 'customer')])
        cust_code_convert = self.env['ss_erp.code.convert'].search(
            [('external_system', 'in', yamasan_gas_type_ids.ids), ('convert_code_type', 'in', cust_code_type_ids.ids)])

        customer_dict = {}
        for customer in external_partners:
            customer_id = cust_code_convert.filtered(lambda x: x.external_code == customer).sorted(
                key=lambda k: (k['priority_conversion']))
            if customer_id:
                customer_internal_code = customer_id[0].internal_code.id
                customer_dict[customer] = customer_internal_code

        # get product
        # products = list(set(self.detail_ids.mapped('item')))
        # product_ids = self.env['product.product'].search_read([('name', 'in', products)],
        #                                                       ['name', 'uom_id', 'list_price', 'standard_price'])
        # product_dict = {}
        # for product in product_ids:
        #     if product['name']:
        #         product_dict[product['name']] = product

        failed_customer_code = []
        failed_customer_cd = []
        success_dict = {}
        for line in exe_data:
            error_message = False
            if not customer_dict.get(line.partner_id, False):
                error_message = '販売店コードの変換に失敗しました。コード変換マスタを確認してください。'
            if line.partner_id not in failed_customer_code:
                if error_message:
                    line.write({
                        'status': 'error',
                        'error_message': error_message
                    })
                    failed_customer_code.append(line.partner_id)
                    if success_dict.get(line.partner_id, False):
                        success_dict.pop(line.partner_id, None)
                    continue
                else:
                    order_data = {
                        'x_organization_id':self.branch_id.id,
                        'partner_id': customer_dict[line.partner_id],
                        'partner_invoice_id': customer_dict[line.partner_id],
                        'partner_shipping_id': customer_dict[line.partner_id],
                        'date_order': self.upload_date,
                        'state': 'draft',
                        'x_no_approval_required_flag': True,
                        'order_line': []
                    }

                    success_dict[line.partner_id] = {
                        'order': order_data,
                        'total_amount_use': line.amount_use,
                        'detail_ids':[]
                    }
            else:
                line.write({
                    'status': 'error',
                    'error_message': error_message
                })

        uom = self.env.ref('uom.product_uom_cubic_meter')
        yamasan_product = self.env.ref('ss_erp.product_product_yamasan_gas')
        for detail in exe_detail_data:
            if detail.customer_cd[0:3] in success_dict:
                line_data = {
                    'product_id': yamasan_product.id,
                    'product_uom': uom.id,
                    'product_uom_qty': float(detail.amount_use),
                }
                success_dict[detail.customer_cd[0:3]]['order']['order_line'].append((0, 0, line_data))
                success_dict[detail.customer_cd[0:3]]['total_amount_use'] -= float(detail.amount_use)
                success_dict[detail.customer_cd[0:3]]['detail_ids'].append(detail.id)
            else:
                failed_customer_cd.append(detail.customer_cd)

        for line in exe_data:
            if success_dict.get(line.partner_id, False):
                order = success_dict[line.partner_id]['order']
                total_amount_use = success_dict[line.partner_id]['total_amount_use']
                standard_price_line={
                    'product_id': yamasan_product.id,
                    'product_uom': uom.id,
                    'product_uom_qty': total_amount_use,
                }
                order['order_line'] = [(0, 0, standard_price_line)] + order['order_line']
                sale_id = self.env['sale.order'].create(order)
                success_dict[line.partner_id]['sale_id'] = sale_id.id
                line.write({
                    'status': 'success',
                    'sale_id': sale_id.id,
                    'processing_date':datetime.now(),
                    'detail_ids':[(6, 0, success_dict[line.partner_id]['detail_ids'])]
                })
                success_dict[line.partner_id].update({
                    'sale_id': sale_id.id,
                    # 'summary_id': line.id
                })


    def import_summary(self):
        return {
            "type": "ir.actions.client",
            "tag": "import",
            "params": {
                "model": "ss_erp.ifdb.yg.summary",
                "context": {
                    "default_import_file_header_model": self._name,
                    "default_import_file_header_id": self.id,
                },
            }
        }

    def import_detail(self):
        return {
            "type": "ir.actions.client",
            "tag": "import",
            "params": {
                "model": "ss_erp.ifdb.yg.detail",
                "context": {
                    "default_import_file_header_model": self._name,
                    "default_import_file_header_id": self.id,
                },
            }
        }
