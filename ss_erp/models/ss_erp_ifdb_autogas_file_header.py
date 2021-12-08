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
        autogas_type_ids = self.env['ss_erp.external.system.type'].search(['code', '=', 'auto_gas_pos'])
        cust_code_type_ids = self.env['ss_erp.convert.code.type'].search(['code', '=', 'customer'])
        cust_code_convert = self.env['ss_erp.code.convert'].search(
            [('external_system', 'in', autogas_type_ids), ('convert_code_type', 'in', cust_code_type_ids)])

        customer_dict = {}
        for customer in external_partners:
            customer_id = cust_code_convert.filtered(lambda x: x.external_code == customer).sorted(
                key=lambda k: (k['priority_conversion']))
            if customer_id:
                customer_dict[customer] = customer_id[0].internal_code

        # get product code convert
        external_products = list(set(exe_data.mapped('product_code')))
        product_code_type_ids = self.env['ss_erp.convert.code.type'].search(['code', '=', 'product'])
        product_code_convert = self.env['ss_erp.code.convert'].search(
            [('external_system', 'in', autogas_type_ids), ('convert_code_type', 'in', product_code_type_ids)])
        product_dict = {}
        for product in external_products:
            product_id = product_code_convert.filtered(lambda x: x.external_code == product).sorted(
                key=lambda k: (k['priority_conversion']))
            if product_id:
                product_dict[product] = product_id[0].internal_code

        uom_id = self.env['uom.uom'].search([('name', '=', 'L')], limit=1)
        if not uom_id:
            raise UserError(_('Lの単位を登録してください！'))

        # Create Sale order
        validate_sos = list(set(exe_data.mapped('validate_so')))
        for so in validate_sos:
            so_line_ids = exe_data.filtered(lambda x: x.validate_so == so)
            check_so = True
            val = []
            for line in so_line_ids:
                error_message = ''
                if not customer_dict.get(line.customer_code):
                    line.status = 'error'
                    error_message = '顧客コードの変換に失敗しました。コード変換マスタを確認してください。'
                    check_so = False
                if product_dict.get(line.product_code):
                    line.status = 'error'
                    error_message += '顧客コードの変換に失敗しました。コード変換マスタを確認してください。'
                    check_so = False
                val.append(((0, 0, {
                    'product_id': product_dict[line.product_code],
                    'product_uom_qty': line.quantity_2,
                    'product_uom': uom_id[0].id,
                })))
                if not check_so:
                    line.error_message = error_message
            if check_so:
                partner_id = customer_dict[so_line_ids[0].customer_code]
                sale_order = {
                    'x_organization_id': self.branch_id,
                    'partner_id': partner_id,
                    'partner_invoice_id': partner_id,
                    'partner_shipping_id': partner_id,
                    'date_order': date_order,
                    'state': 'draft',
                    'no_approval_required_flag': True,
                    'order_line': val,
                }
                order_id = self.env['sale.order'].create(sale_order)
                for line in so_line_ids:
                    line.status = 'success'
                    line.sale_id = order_id.id

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

            if line.validate_so not in order_to_create:
                order_to_create.append(line.validate_so)
                if not detail:
                    so = {
                        'x_organization_id': self.branch_id,
                        'partner_id': partner_id,
                        'partner_invoice_id': partner_id,
                        'partner_shipping_id': partner_id,
                        'date_order': line.calendar_date,
                        'state': 'draft',
                        'no_approval_required_flag': True,
                    }
                    detail = []
                else:
                    if last_order_ref and last_order_ref not in failed_order:
                        so['order_line'] = detail
                        order_id = self.env['sale.order'].create(so)
                        success_order_dict[last_validate_so] = order_id.id

            if not customer_dict.get(line.customer_code):
                line.status = 'error'
                error_message = '顧客コードの変換に失敗しました。コード変換マスタを確認してください。'
            if not product_dict.get(line.product_code):
                line.status = 'error'
                error_message += '顧客コードの変換に失敗しました。コード変換マスタを確認してください。'
            if error_message:
                line.error_message=error_message
                if line.validate_so not in failed_order:
                    failed_order.append(line.validate_so)
            else:
                val.append(((0, 0, {
                    'product_id': product_dict[line.product_code],
                    'product_uom_qty': line.quantity_2,
                    'product_uom': uom_id[0].id,
                })))
                last_order_ref = line.validate_so
            if last_order_ref and last_order_ref not in failed_order and count == len_list:
                so['order_line'] = detail
                order_id = self.env['sale.order'].create(so)
                success_order_dict[last_validate_so] = order_id.id
            count += 1

        for line in exe_data:
            if line.validate_so not in failed_order:
                line.status = 'success'
                line.sale_id = success_order_dict[validate_so]