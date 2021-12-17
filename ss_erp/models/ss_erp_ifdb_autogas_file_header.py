from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime


class IFDBAutogasFileHeader(models.Model):
    _name = "ss_erp.ifdb.autogas.file.header"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Autogas File Header"

    upload_date = fields.Datetime(
        string="アップロード日時",
        index=True,
        readonly=True,
		default=fields.Datetime.now()
    )
    name = fields.Char(
        string="名称",
        required=True,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="担当者",
        required=True,
        index=True
    )
    branch_id = fields.Many2one(
        comodel_name="ss_erp.organization",
        string="支店",
        index=True
    )
    status = fields.Selection(
        selection=[
            ("wait", "処理待ち"),
            ("success", "成功"),
            ("error", "エラーあり")
        ],
        string="ステータス",
        index=True,
        default="wait",
        compute='_compute_status'
    )
    autogas_data_record_ids = fields.One2many(
        comodel_name="ss_erp.ifdb.autogas.file.data.rec",
        inverse_name="autogas_file_header_id",
        string="データレコード"
    )

    has_data_import = fields.Boolean(compute='_compute_has_data_import')

    #
    @api.depends('autogas_data_record_ids')
    def _compute_has_data_import(self):
        for record in self:
            if record.autogas_data_record_ids:
                record.has_data_import = True
            else:
                record.has_data_import = False

    _sql_constraints = [
        (
            "name_uniq",
            "UNIQUE(name)",
            "File Header Name is used for searching, please make it unique!"
        )
    ]

    @api.depends('autogas_data_record_ids.status')
    def _compute_status(self):
        for record in self:
            if record.autogas_data_record_ids:
                status_list = record.autogas_data_record_ids.mapped('status')
                record.status = "success"
                if "error" in status_list:
                    record.status = "error"
                elif "wait" in status_list:
                    record.status = "wait"
            else:
                record.status = "wait"

    def action_processing_excution(self):
        for r in self:
            r._processing_excution()

    def action_import(self):
        self.ensure_one()
        self.upload_date = fields.Datetime.now()
        return {
            "type": "ir.actions.client",
            "tag": "import",
            "params": {
                "model": "ss_erp.ifdb.autogas.file.data.rec",
                "context": {
                    "default_import_file_header_model": self._name,
                    "default_import_file_header_id": self.id,
                },
            }
        }

    def _processing_excution(self):
        self.ensure_one()
        exe_data = self.autogas_data_record_ids.filtered(lambda line: line.status in ('wait', 'error')).sorted(
            key=lambda k: (k['validate_so'],k['calendar_date'], k['card_number'],))

        # get customer code convert
        external_partners = list(set(exe_data.mapped('customer_code')))
        autogas_type_ids = self.env['ss_erp.external.system.type'].search([('code', '=', 'auto_gas_pos')]).mapped('id')
        cust_code_type_ids = self.env['ss_erp.convert.code.type'].search([('code', '=', 'customer')]).mapped('id')
        cust_code_convert = self.env['ss_erp.code.convert'].search_read(
            [('external_system', 'in', autogas_type_ids), ('convert_code_type', 'in', cust_code_type_ids)],['external_code','internal_code'])

        customer_dict = {}
        for customer in cust_code_convert:
            if not customer_dict.get(customer['external_code']):
                if customer['external_code']:
                    internal_code = customer['internal_code'].split(",")[1]
                    customer_dict[customer['external_code']] = int(internal_code)

        # get product code convert
        external_products = list(set(exe_data.mapped('product_code')))
        product_code_type_ids = self.env['ss_erp.convert.code.type'].search([('code', '=', 'product')]).mapped('id')
        product_code_convert = self.env['ss_erp.code.convert'].search_read(
            [('external_system', 'in', autogas_type_ids), ('convert_code_type', 'in', product_code_type_ids)],['external_code','internal_code'])
        product_dict = {}
        for product in product_code_convert:
            if not product_dict.get(product['external_code']):
                if product['external_code']:
                    internal_code = product['internal_code'].split(",")[1]
                    product_dict[product['external_code']] = int(internal_code)

        uom_id = self.env['uom.uom'].search([('name', '=', 'L')], limit=1)
        if not uom_id:
            raise UserError(_('Lの単位を登録してください！'))


        # Create sale order
        failed_so = []
        success_dict = {}
        for line in exe_data:
            error_message = False
            if not customer_dict.get(line.customer_code):
                line.status = 'error'
                error_message = '顧客コードの変換に失敗しました。コード変換マスタを確認してください。'
            if not product_dict.get(line.product_code):
                line.status = 'error'
                if error_message:
                    error_message += '商品コードの変換に失敗しました。コード変換マスタを確認してください。'
                else:
                    error_message = '商品コードの変換に失敗しました。コード変換マスタを確認してください。'

            if not error_message:
                quantity = float(line.quantity_2)/100
                order_line = {
                    'product_id': product_dict[line.product_code],
                    'product_uom_qty':quantity,
                    'product_uom': uom_id[0].id,
                }
                order_date = datetime.strptime(line.calendar_date,'%y%m%d')
                if not success_dict.get(line.validate_so):
                    so = {
                            'x_organization_id': self.branch_id.id,
                            'partner_id': customer_dict.get(line.customer_code),
                            'partner_invoice_id': customer_dict.get(line.customer_code),
                            'partner_shipping_id': customer_dict.get(line.customer_code),
                            'date_order': order_date,
                            'state': 'draft',
                            'x_no_approval_required_flag': True,
                            'order_line': [(0, 0, order_line)]
                        }
                    success_dict[line.validate_so] = so
                else:
                    success_dict[line.validate_so]['order_line'].append((0, 0, order_line))
            else:
                if line.validate_so not in failed_so:
                    failed_so.append(line.validate_so)
                if success_dict.get(line.validate_so, False):
                    success_dict.pop(line.validate_so, None)
                line.write({
                    'status': 'error',
                    'error_message': error_message
                })

        for key, value in success_dict.items():
            sale_id = self.env['sale.order'].create(value)
            success_dict[key]['sale_id'] = sale_id.id

        success_list = success_dict.keys()
        for line in exe_data:
            if line.validate_so in success_list:
                line.status = 'success'
                line.sale_id = success_dict[line.validate_so]['sale_id']
                line.processing_date = datetime.now()