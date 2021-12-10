from odoo import models, fields, api, _


class IFDBPropaneSalesHeader(models.Model):
    _name = 'ss_erp.ifdb.propane.sales.header'
    _description = 'Propane sales'

    name = fields.Char(string='Name')
    upload_date = fields.Datetime(
        string='Upload date and time', index=True, required=True)
    user_id = fields.Many2one('res.users', string='Manager')
    branch_id = fields.Many2one('ss_erp.organization', string='Branch')
    status = fields.Selection([
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり'),
    ], string='Status', default='wait', index=True)
    sales_detail_ids = fields.One2many(
        'ss_erp.ifdb.propane.sales.detail', 'propane_sales_header_id',
        string='Propane sales file header')

    def btn_processing_execution(self):
        for record in self:
            record._processing_excution()

    def _processing_excution(self):
        self.ensure_one()
        exe_data = self.sales_detail_ids.filtered(lambda line: line.status in ('wait', 'error')).sorted(
            key=lambda k: (k['customer_business_partner_code']))

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
                error_message = 'Account C does not exist in the contact master.'
            if int(line.customer_branch_code) not in organization_list:
                error_message += 'Branch office C does not exist in the organization master.'
            if int(line.commercial_branch_code) not in organization_list:
                error_message += 'Branch C does not exist in the organization master.'
            if int(line.commercial_product_code) not in product_list:
                error_message += 'Product C does not exist in the product master.'
            if int(line.unit_code) not in uom_list:
                error_message += 'Unit C does not exist in the product unit master.'

            if line.customer_business_partner_code not in failed_customer_code:
                if error_message:
                    line.write({
                        'status': 'error',
                        'error_message': error_message
                    })
                    failed_customer_code.append(line.customer_business_partner_code)
                    if success_dict.get(line.customer_business_partner_code, False):
                        success_dict.pop(line.customer_business_partner_code, None)
                    continue
                else:
                    if not success_dict.get(line.customer_business_partner_code):
                        so = {
                            'partner_id': int(line.customer_business_partner_code),
                            'order_line': [(0, 0, {
                                'product_id': int(line.commercial_product_code),
                                'product_uom_qty': 1,
                                'product_uom': int(line.unit_code)
                            })],
                        }
                        success_dict[line.customer_business_partner_code] = {
                            'order': so,
                            'success': [line.id]
                        }
                    else:
                        order_line = {
                            'product_id': int(line.commercial_product_code),
                            'product_uom_qty': 1,
                            'product_uom': int(line.unit_code)
                        }
                        success_dict[line.customer_business_partner_code]['order']['order_line'].append(
                            (0, 0, order_line))
                        success_dict[line.customer_business_partner_code]['success'].append(line.id)
            else:
                line.write({
                    'status': 'error',
                    'error_message': error_message
                })

        for line in exe_data:
            if success_dict.get(line.customer_business_partner_code, False):
                if success_dict.get(line.customer_business_partner_code).get('sale_id', False):
                    sale_id = success_dict.get(line.customer_business_partner_code).get('sale_id')
                    line.write({
                        'status': 'success',
                        'sale_id': sale_id
                    })
                else:
                    sale_id = self.env['sale.order'].create(success_dict[line.customer_business_partner_code]['order'])
                    success_dict[line.customer_business_partner_code]['sale_id'] = sale_id.id
                    line.write({
                        'status': 'success',
                        'sale_id': sale_id.id
                    })
