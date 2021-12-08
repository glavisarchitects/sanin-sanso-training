from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime


class IFDBPowerNetSalesHeader(models.Model):
    _name = 'ss_erp.ifdb.powernet.sales.header'
    _description = 'IFDB PowerNet Sales Header'

    upload_date = fields.Datetime('Upload date and time', index=True)
    name = fields.Char('Name')
    user_id = fields.Many2one('res.users', 'Person in charge', index=True)
    branch_id = fields.Many2one('ss_erp.organization', 'Branch', index=True)
    status = fields.Selection(selection=[
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラー')
    ], string='Status', default="wait")

    powernet_sale_record_ids = fields.One2many(
        comodel_name="ss_erp.ifdb.powernet.sales.detail",
        inverse_name="powernet_sales_header_id",
        string="PowerNet Sale Record details"
    )

    def action_import(self):
        self.ensure_one()
        self.upload_date = fields.Datetime.now()
        return {
            "type": "ir.actions.client",
            "tag": "import",
            "params": {
                "model": "ss_erp.ifdb.powernet.sales.detail",
                "context": {
                    "default_import_file_header_model": self._name,
                    "default_import_file_header_id": self.id,
                },
            }
        }

    def processing_execution(self):
        for r in self:
            r._processing_excution()

    def _processing_excution(self):
        self.ensure_one()

        customer_id = self.env['ir.config_parameter'].sudo().get_param('powernet.direct.sales.dummy.customer_id')
        if not customer_id:
            raise UserError(
                _('直売売上用の顧客コードの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。（powernet.direct.sales.dummy.customer_id）'))
        exe_data = self.powernet_sale_record_ids.filtered(lambda line: line.status in ('wait', 'error')).sorted(
            key=lambda k: (k['sales_date'], k['customer_code'], k['data_types']))

        # Get list product uom exchange
        powernet_type_ids = self.env['ss_erp.external.system.type'].search([('code', '=', 'power_net')])
        convert_product_unit_type_ids = self.env['ss_erp.convert.code.type'].search([('code', '=', 'product_unit')])
        uom_code_convert = self.env['ss_erp.code.convert'].search_read([('external_system', 'in', powernet_type_ids),('convert_code_type', 'in', convert_product_unit_type_ids)],['external_code','internal_code'])
        uom_dict = {}
        for uom in uom_code_convert:
            if not uom_dict.get(uom.external_code):
                if uom['external_code']:
                    uom_dict[uom['external_code']] = uom['internal_code']

        product_product_ids = self.env['product.product'].search_read([],['default_code'])
        product_dict = {}
        for product in product_product_ids:
            if product['default_code']:
                product_dict[product['default_code']] = product['id']

        # Create sale order
        order_to_create=[]
        failed_order = []
        success_order_dict = {}
        detail=[]
        last_order_ref = False
        count = 0
        len_list = len(exe_data)
        for line in exe_data:
            error_message = False

            if line.sale_ref not in order_to_create:
                order_to_create.append(line.sale_ref)
                if not detail:
                    so = {
                        'x_organization_id': self.branch_id,
                        'partner_id': customer_id,
                        'partner_invoice_id': customer_id,
                        'partner_shipping_id': customer_id,
                        'date_order': self.upload_date,
                        'state': 'draft',
                        'no_approval_required_flag': True,
                    }
                    detail = []
                else:
                    if last_order_ref and last_order_ref not in failed_order:
                        so['order_line'] = detail
                        order_id = self.env['sale.order'].create(so)
                        success_order_dict[last_sale_ref] = order_id.id
            if not product_dict.get(line.product_code):
                line.status = 'error'
                error_message = '商品コードがプロダクトマスタに存在しません。'

            if not uom_dict.get(line.unit_code):
                line.status = 'error'
                error_message += '単位コードの変換に失敗しました。コード変換マスタを確認してください。'
            if error_message:
                line.error_message=error_message
                if line.sale_ref not in failed_order:
                    failed_order.append(line.sale_ref)
            else:
                detail.append(((0, 0, {
                    'product_id': product_dict[line.product_code],
                    'product_uom_qty': line.quantity,
                    'product_uom': uom_dict[line.unit_code],
                })))
                last_order_ref = line.sale_ref
            if last_order_ref and last_order_ref not in failed_order and count == len_list:
                so['order_line'] = detail
                order_id = self.env['sale.order'].create(so)
                success_order_dict[last_sale_ref] = order_id.id
            count += 1

        for line in exe_data:
            if line.sale_ref not in failed_order:
                line.status = 'success'
                line.sale_id = success_order_dict[sale_ref]