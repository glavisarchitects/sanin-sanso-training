# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError

class IFDBYGHeader(models.Model):
    _name = 'ss_erp.ifdb.yg.header'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'ヤマサンガスヘッダ'

    name = fields.Char(string='名称')
    upload_date = fields.Datetime(
        string='アップロード日時', index=True, required=True,
        default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='担当者', tracking=True)
    branch_id = fields.Many2one(
        'ss_erp.organization', string='支店', tracking=True)
    status = fields.Selection([
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり'),
    ], string='ステータス', default='wait', index=True,store=True, compute='_compute_status')
    meter_reading_date = fields.Date(string='検針年月', index=True)
    summary_ids = fields.One2many(
        'ss_erp.ifdb.yg.summary', 'header_id', '検針集計表')
    detail_ids = fields.One2many(
        'ss_erp.ifdb.yg.detail', 'header_id', '検針明細表')

    has_data_import = fields.Boolean(compute='_compute_has_data_import')

    @api.constrains("branch_id")
    def _check_default_warehouse(self):
        for record in self:
            if not record.branch_id.warehouse_id:
                raise ValidationError(_("対象の支店にデフォルト倉庫が設定されていません。組織マスタの設定を確認してください。"))

    @api.depends('detail_ids')
    def _compute_has_data_import(self):
        for record in self:
            if record.detail_ids and record.summary_ids:
                record.has_data_import = False
            else:
                record.has_data_import = True

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
        yamasan_gas_type_ids = self.env['ss_erp.external.system.type'].search([('code', '=', 'yamasan_gas')])
        cust_code_type_ids = self.env['ss_erp.convert.code.type'].search([('code', '=', 'customer')])
        cust_code_convert = self.env['ss_erp.code.convert'].search(
            [('external_system', 'in', yamasan_gas_type_ids.ids),
             ('convert_code_type', 'in', cust_code_type_ids.ids)]).sorted(
            key=lambda k: (k['external_code'], k['priority_conversion']))

        customer_dict = {}
        for customer in cust_code_convert:
            if not customer_dict.get(customer['external_code']):
                customer_dict[customer['external_code']] = customer['internal_code'].id

        failed_customer_code = []
        failed_customer_cd = []
        success_dict = {}
        for line in exe_data:
            error_message = False
            partner_id = str(line.partner_id)
            if not customer_dict.get(partner_id, False):
                error_message = '販売店コードの変換に失敗しました。コード変換マスタを確認してください。'
            if line.partner_id not in failed_customer_code:
                if error_message:
                    line.write({
                        'status': 'error',
                        'error_message': error_message
                    })
                    failed_customer_code.append(partner_id)
                    if success_dict.get(partner_id, False):
                        success_dict.pop(partner_id, None)
                    continue
                else:
                    order_data = {
                        'x_organization_id': self.branch_id.id,
                        'warehouse_id': self.branch_id.warehouse_id.id,
                        'partner_id': customer_dict[line.partner_id],
                        'partner_invoice_id': customer_dict[line.partner_id],
                        'partner_shipping_id': customer_dict[line.partner_id],
                        'date_order': self.meter_reading_date,
                        'state': 'draft',
                        'x_no_approval_required_flag': True,
                        'order_line': []
                    }

                    success_dict[partner_id] = {
                        'order': order_data,
                        'total_amount_use': line.amount_use,
                        'detail_ids': []
                    }
            else:
                if error_message:
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
            partner_id = str(line.partner_id)
            if success_dict.get(partner_id, False):
                order = success_dict[partner_id]['order']
                total_amount_use = success_dict[partner_id]['total_amount_use']
                standard_price_line = {
                    'product_id': yamasan_product.id,
                    'product_uom': uom.id,
                    'product_uom_qty': total_amount_use,
                }
                order['order_line'] = [(0, 0, standard_price_line)] + order['order_line']
                sale_id = self.env['sale.order'].create(order)
                success_dict[partner_id]['sale_id'] = sale_id.id
                line.write({
                    'status': 'success',
                    'sale_id': sale_id.id,
                    'processing_date': datetime.now(),
                    'detail_ids': [(6, 0, success_dict[partner_id]['detail_ids'])],
                    'error_message': False
                })
                success_dict[partner_id].update({
                    'sale_id': sale_id.id,
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
