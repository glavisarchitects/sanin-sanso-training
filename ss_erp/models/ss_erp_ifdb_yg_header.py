# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class IFDBYGHeader(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'ss_erp.ifdb.yg.header'
    _description = 'Yamasan Gas Supply Header'

    name = fields.Char(string='Name')
    upload_date = fields.Datetime(
        string='Upload date and time', index=True, required=True)
    user_id = fields.Many2one('res.users', string='Manager', tracking=True)
    branch_id = fields.Many2one(
        'ss_erp.organization', string='Branch', tracking=True)
    status = fields.Selection([
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり'),
    ], string='Status', default='wait', index=True)
    meter_reading_date = fields.Date(string='Meter reading date', index=True)
    summary_ids = fields.One2many(
        'ss_erp.ifdb.yg.summary', 'header_id', 'Meter reading summary table')
    detail_ids = fields.One2many(
        'ss_erp.ifdb.yg.detail', 'header_id', 'Meter reading detail table')

    def btn_processing_execution(self):
        for record in self:
            record._processing_excution()

    def _processing_excution(self):
        self.ensure_one()
        exe_data = self.summary_ids.filtered(lambda line: line.status in ('wait', 'error')).sorted(
            key=lambda k: (k['partner_id']))

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
        products = list(set(self.summary_ids.mapped('detail_ids').mapped('item')))
        product_ids = self.env['product.product'].search_read([('name', 'in', products)],
                                                              ['name', 'uom_id', 'list_price', 'standard_price'])
        product_dict = {}
        for product in product_ids:
            if product['name']:
                product_dict[product['name']] = product

        failed_customer_code = []
        success_dict = {}
        for line in exe_data:
            error_message = False
            if not customer_dict.get(line.partner_id, False):
                error_message = 'Failed to convert the store code. Check the code conversion master.'
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
                        'partner_id': customer_dict[line.partner_id]
                    }
                    detail_data = line.detail_ids.filtered(lambda l: l.status in ('wait', 'error')).sorted(
                        key=lambda k: (k['customer_cd']))
                    prod = False
                    total_amount_use = 0
                    order_line = []
                    success_detail = []
                    for detail in detail_data:
                        if detail.customer_cd[0:3] == line.partner_id:
                            total_amount_use += detail.amount_use
                            if product_dict.get(detail.item, False):
                                prod = product_dict[detail.item]
                                line_data = {
                                    'product_id': product_dict[detail.item]['id'],
                                    'product_uom_qty': 1,
                                    'product_uom': product_dict[detail.item]['uom_id'][0],
                                    'price_unit': detail.amount_use * product_dict[detail.item]['list_price'],
                                }
                                order_line.append((0, 0, line_data))
                                success_detail.append(detail.customer_cd)
                        else:
                            continue
                    if prod:
                        order_line.append((0, 0, {
                            'product_id': prod['id'],
                            'product_uom_qty': 1,
                            'product_uom': prod['uom_id'][0],
                            'price_unit': (line.amount_use - total_amount_use) * prod['standard_price'],
                        }))
                    order_data['order_line'] = order_line
                    success_dict[line.partner_id] = {
                        'order': order_data,
                        'success_detail': success_detail,
                        'success': [line.id]
                    }
            else:
                line.write({
                    'status': 'error',
                    'error_message': error_message
                })

        for line in exe_data:
            if success_dict.get(line.partner_id, False):
                if success_dict.get(line.partner_id).get('sale_id', False):
                    sale_id = success_dict.get(line.partner_id).get('sale_id')
                    line.write({
                        'status': 'success',
                        'sale_id': sale_id
                    })
                    for detail in line.detail_ids:
                        if detail.customer_cd in success_dict[line.partner_id]['success_detail']:
                            detail.write({
                                'status': 'success',
                                'sale_id': sale_id
                            })
                else:
                    sale_id = self.env['sale.order'].create(success_dict[line.partner_id]['order'])
                    success_dict[line.partner_id]['sale_id'] = sale_id.id
                    line.write({
                        'status': 'success',
                        'sale_id': sale_id.id
                    })
                    for detail in line.detail_ids:
                        if detail.customer_cd in success_dict[line.partner_id]['success_detail']:
                            detail.write({
                                'status': 'success',
                                'sale_id': sale_id
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
