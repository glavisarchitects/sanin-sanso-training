from odoo import models, fields, api, _
from datetime import datetime

class IFDBPropaneSalesHeader(models.Model):
    _name = 'ss_erp.ifdb.propane.sales.header'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Propane sales'

    name = fields.Char(string='名称')
    upload_date = fields.Datetime(
        string='アップロード日時', index=True, required=True,
		default=fields.Datetime.now())
    user_id = fields.Many2one('res.users', string='担当者')
    branch_id = fields.Many2one('ss_erp.organization', string='支店')
    status = fields.Selection([
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり'),
    ], string='ステータス', default='wait', index=True,compute='_compute_status')
    sales_detail_ids = fields.One2many(
        'ss_erp.ifdb.propane.sales.detail', 'propane_sales_header_id',
        string='Propane sales file header')
    has_data_import = fields.Boolean(compute='_compute_has_data_import')

    #
    @api.depends('sales_detail_ids')
    def _compute_has_data_import(self):
        for record in self:
            if record.sales_detail_ids:
                record.has_data_import = True
            else:
                record.has_data_import = False


    _sql_constraints = [
        (
            "name_unique",
            "UNIQUE(name)",
            "Name is used for searching, please make it unique!"
        ),
    ]

    @api.depends('sales_detail_ids.status')
    def _compute_status(self):
        for record in self:
            if record.sales_detail_ids:
                status_list = record.sales_detail_ids.mapped('status')
                record.status = "success"
                if "error" in status_list:
                    record.status = "error"
                elif "wait" in status_list:
                    record.status = "wait"
            else:
                record.status = "wait"

    def action_import(self):
        return {
            "type": "ir.actions.client",
            "tag": "import",
            "params": {
                "model": "ss_erp.ifdb.propane.sales.detail",
                "context": {
                    "default_import_file_header_model": self._name,
                    "default_import_file_header_id": self.id,
                },
            }
        }

    def btn_processing_execution(self):
        for record in self:
            record._processing_excution()

    def _processing_excution(self):
        self.ensure_one()
        exe_data = self.sales_detail_ids.filtered(lambda line: line.status in ('wait', 'error')).sorted(
            key=lambda k: (k['slip_date'],k['customer_business_partner_code']))

        partner_ids = self.env['res.partner'].search_read([], ['id'])
        partner_list = []
        for partner in partner_ids:
            if partner['id'] not in partner_list:
                partner_list.append(partner['id'])

        uom_uom_ids = self.env['uom.uom'].search_read([], ['id'])
        uom_list = []
        for uom in uom_uom_ids:
            if uom['id'] not in uom_list:
                uom_list.append(uom['id'])

        product_product_ids = self.env['product.product'].search_read([], ['id'])
        product_list = []
        for product in product_product_ids:
            if product['id'] and product['id'] not in product_list:
                product_list.append(product['id'])

        organization_ids = self.env['ss_erp.organization'].search_read([])
        organization_list = []
        for organization_id in organization_ids:
            if organization_id['id'] and organization_id['id'] not in organization_list:
                organization_list.append(organization_id['id'])

        failed_customer_code = []
        success_dict = {}
        for line in exe_data:
            error_message = False
            if int(line.customer_business_partner_code) not in partner_list:
                error_message = '顧取引先Ｃが連絡先マスタに存在しません。'

            if int(line.customer_branch_code) not in organization_list:
                if error_message:
                    error_message += '顧支店Ｃが組織マスタに存在しません。'
                else:
                    error_message = '顧支店Ｃが組織マスタに存在しません。'

            if int(line.codeommercial_branch_code) not in organization_list:
                if error_message:
                    error_message += '商支店Ｃが組織マスタに存在しません。'
                else:
                    error_message = '商支店Ｃが組織マスタに存在しません。'

            if int(line.codeommercial_product_code) not in product_list:
                if error_message:
                    error_message += '商商品Ｃがプロダクトマスタに存在しません。'
                else:
                    error_message = '商商品Ｃがプロダクトマスタに存在しません。'

            if int(line.unit_code) not in uom_list:
                if error_message:
                    error_message += '単位Ｃがプロダクト単位マスタに存在しません。'
                else:
                    error_message = '単位Ｃがプロダクト単位マスタに存在しません。'

            if line.slip_date and line.customer_business_partner_code:
                key = str(line.slip_date) + '_' + str(line.customer_business_partner_code)

                if line.customer_business_partner_code not in failed_customer_code:
                    if error_message:
                        line.write({
                            'status': 'error',
                            'error_message': error_message
                        })
                        failed_customer_code.append(line.customer_business_partner_code)
                        if success_dict.get(key, False):
                            success_dict.pop(key, None)
                        continue
                    else:
                        if not success_dict.get(key):
                            slip_date=datetime.strptime(line.slip_date,'%Y/%m/%d')
                            so = {
                                'partner_id': int(line.customer_business_partner_code),
                                'partner_invoice_id': int(line.customer_business_partner_code),
                                'partner_shipping_id': int(line.customer_business_partner_code),
                                'date_order': slip_date,
                                'order_line': [(0, 0, {
                                    'product_id': int(line.codeommercial_product_code),
                                    'product_uom_qty': line.quantity,
                                    'product_uom': int(line.unit_code)
                                })],
                            }
                            success_dict[key] = {
                                'order': so,
                                'success': [line.id]
                            }
                        else:
                            order_line = {
                                'product_id': int(line.codeommercial_product_code),
                                'product_uom_qty': line.quantity,
                                'product_uom': int(line.unit_code)
                            }
                            success_dict[key]['order']['order_line'].append(
                                (0, 0, order_line))
                            success_dict[key]['success'].append(line.id)
                else:
                    line.write({
                        'status': 'error',
                        'error_message': error_message
                    })

        for key, value in success_dict.items():
            sale_id = self.env['sale.order'].create(value['order'])
            success_dict[key]['sale_id'] = sale_id.id

        for line in exe_data:
            key = str(line.slip_date) + '_' + str(line.customer_business_partner_code)
            if success_dict.get(key):
                line.write({
                    'status': 'success',
                    'sale_id': success_dict[key]['sale_id'],
                    'processing_date':datetime.now(),
                    'error_message': False
                })
