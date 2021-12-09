from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime


class IFDBAutogasFileHeader(models.Model):
    _name = "ss_erp.ifdb.autogas.file.header"
    _description = "Autogas File Header"

    upload_date = fields.Datetime(
        string="アップロード日時",
        index=True,
        readonly=True
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
        required=True,
        index=True,
        default="wait"
    )
    autogas_data_record_ids = fields.One2many(
        comodel_name="ss_erp.ifdb.autogas.file.data.rec",
        inverse_name="autogas_file_header_id",
        string="データレコード"
    )

    _sql_constraints = [
        (
            "name_uniq",
            "UNIQUE(name)",
            "File Header Name is used for searching, please make it unique!"
        )
    ]

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
            key=lambda k: (k['calendar_date'], k['card_number']))

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
        product_code_type_ids = self.env['ss_erp.convert.code.type'].search([('code', '=', 'product')])
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
        order_to_create=[]
        failed_order = []
        success_order_dict = {}
        detail=[]
        last_validate_so = False
        count = 0
        len_list = len(exe_data)
        for line in exe_data:
            error_message = False
            if not customer_dict.get(line.customer_code):
                line.status = 'error'
                error_message = '顧客コードの変換に失敗しました。コード変換マスタを確認してください。'
            if not product_dict.get(line.product_code):
                line.status = 'error'
                if error_message:
                    error_message+= '商品コードの変換に失敗しました。コード変換マスタを確認してください。'
                else:
                    error_message= '商品コードの変換に失敗しました。コード変換マスタを確認してください。'

            if line.validate_so not in order_to_create:
                order_to_create.append(line.validate_so)
                if not detail and not error_message:
                    date = datetime.strptime(line.calendar_date,'%y%m%d') if line.calendar_date else datetime.now()
                    so = {
                        'x_organization_id': self.branch_id,
                        'partner_id': customer_dict.get(line.customer_code),
                        'partner_invoice_id': customer_dict.get(line.customer_code),
                        'partner_shipping_id': customer_dict.get(line.customer_code),
                        'date_order': date,
                        'state': 'draft',
                        'no_approval_required_flag': True,
                    }
                    detail = []
                else:
                    if last_validate_so and last_validate_so not in failed_order:
                        so['order_line'] = detail
                        order_id = self.env['sale.order'].create(so)
                        success_order_dict[last_validate_so] = order_id.id
            if error_message:
                line.error_message=error_message
                if line.validate_so not in failed_order:
                    failed_order.append(line.validate_so)
            else:
                detail.append(((0, 0, {
                    'product_id': product_dict[line.product_code],
                    'product_uom_qty': line.quantity_2,
                    'product_uom': uom_id[0].id,
                })))
                last_validate_so = line.validate_so
            if last_validate_so and last_validate_so not in failed_order and count == len_list:
                so['order_line'] = detail
                order_id = self.env['sale.order'].create(so)
                success_order_dict[last_validate_so] = order_id.id
            count += 1

        for line in exe_data:
            if line.validate_so not in failed_order:
                line.status = 'success'
                line.sale_id = success_order_dict[line.validate_so]
                line.processing_date = datetime.now()