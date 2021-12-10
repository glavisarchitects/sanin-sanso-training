from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime


class IFDBPowerNetSalesHeader(models.Model):
    _name = 'ss_erp.ifdb.powernet.sales.header'
    _description = 'IFDB PowerNet Sales Header'

    upload_date = fields.Datetime('アップロード日時', index=True)
    name = fields.Char('名称')
    user_id = fields.Many2one('res.users', '担当者', index=True)
    branch_id = fields.Many2one('ss_erp.organization', '支店', index=True)
    status = fields.Selection(selection=[
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり')
    ], string='ステータス', default="wait",compute='_compute_status')

    powernet_sale_record_ids = fields.One2many(
        comodel_name="ss_erp.ifdb.powernet.sales.detail",
        inverse_name="powernet_sales_header_id",
        string="PowerNet販売記録の詳細"
    )
    _sql_constraints = [
        (
            "name_uniq",
            "UNIQUE(name)",
            "File Header Name is used for searching, please make it unique!"
        )
    ]

    @api.depends('powernet_sale_record_ids.status')
    def _compute_status(self):
        for record in self:
            record.status = 'wait'
            if record.powernet_sale_record_ids:
                status_list = record.powernet_sale_record_ids.mapped('status')
                if 'error' in status_list:
                    record.status = 'error'
                elif 'wait' in status_list:
                    record.status = 'wait'
                else:
                    record.status = 'success'

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

        customer_code = self.env['ir.config_parameter'].sudo().get_param('powernet.direct.sales.dummy.customer_id')
        customer_id = self.env['res.partner'].search([('ref','=',customer_code)],limit=1)

        if not customer_id:
            raise UserError(
                _('直売売上用の顧客コードの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。（powernet.direct.sales.dummy.customer_id）'))
        exe_data = self.powernet_sale_record_ids.filtered(lambda line: line.status in ('wait', 'error')).sorted(
            key=lambda k: (k['sale_ref'],k['sales_date'], k['customer_code'], k['data_types']))

        # Get list product uom exchange
        powernet_type_ids = self.env['ss_erp.external.system.type'].search([('code', '=', 'power_net')]).mapped('id')
        convert_product_unit_type_ids = self.env['ss_erp.convert.code.type'].search([('code', '=', 'product_unit')]).mapped('id')
        uom_code_convert = self.env['ss_erp.code.convert'].search_read([('external_system', 'in', powernet_type_ids),('convert_code_type', 'in', convert_product_unit_type_ids)],['external_code','internal_code'])
        uom_dict = {}
        for uom in uom_code_convert:
            if not uom_dict.get(uom['external_code']):
                if uom['external_code']:
                    internal_code = uom['internal_code'].split(",")[1]
                    uom_dict[uom['external_code']] = int(internal_code)

        product_product_ids = self.env['product.product'].search_read([],['default_code'])
        product_dict = {}
        for product in product_product_ids:
            if product['default_code']:
                product_dict[product['default_code']] = product['id']

        failed_so = []
        success_dict = {}
        for line in exe_data:
            error_message = False
            if not product_dict.get(line.product_code):
                line.status = 'error'
                error_message = '商品コードがプロダクトマスタに存在しません。'

            if not uom_dict.get(line.unit_code):
                line.status = 'error'
                if error_message:
                    error_message+= '単位コードの変換に失敗しました。コード変換マスタを確認してください。'
                else:
                    error_message= '単位コードの変換に失敗しました。コード変換マスタを確認してください。'
            if not error_message:
                order_line = {
                    'product_id': product_dict[line.product_code],
                    'product_uom_qty': line.quantity,
                    'product_uom': uom_dict[line.unit_code],
                }
                if not success_dict.get(line.sale_ref):
                    so = {
                            'x_organization_id': self.branch_id.id,
                            'partner_id': customer_id[0].id,
                            'partner_invoice_id': customer_id[0].id,
                            'partner_shipping_id': customer_id[0].id,
                            'date_order': self.upload_date,
                            'state': 'draft',
                            'x_no_approval_required_flag': True,
                            'order_line': [(0, 0, order_line)]
                        }
                    success_dict[line.sale_ref] = so
                else:
                    success_dict[line.sale_ref]['order_line'].append((0, 0, order_line))
            else:
                if line.sale_ref not in failed_so:
                    failed_so.append(line.sale_ref)
                if success_dict.get(line.sale_ref, False):
                    success_dict.pop(line.sale_ref, None)
                line.write({
                    'status': 'error',
                    'error_message': error_message
                })

        for key, value in success_dict.items():
            sale_id = self.env['sale.order'].create(value)
            success_dict[key]['sale_id'] = sale_id.id

        success_list = success_dict.keys()
        for line in exe_data:
            if line.sale_ref in success_list:
                line.status = 'success'
                line.sale_id = success_dict[line.sale_ref]['sale_id']
                line.processing_date = datetime.now()