from odoo import _, api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime


class IFDBPowerNetSalesHeader(models.Model):
    _name = 'ss_erp.ifdb.powernet.sales.header'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'PowerNetヘッダ'

    upload_date = fields.Datetime('アップロード日時', index=True,
                                  default=fields.Datetime.now)
    name = fields.Char('名称')
    user_id = fields.Many2one('res.users', '担当者', index=True)
    branch_id = fields.Many2one('ss_erp.organization', '支店', index=True)
    status = fields.Selection(selection=[
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり')
    ], string='ステータス', default="wait", store=True,compute='_compute_status')

    powernet_sale_record_ids = fields.One2many(
        comodel_name="ss_erp.ifdb.powernet.sales.detail",
        inverse_name="powernet_sales_header_id",
        string="PowerNet販売記録の詳細"
    )
    has_data_import = fields.Boolean(compute='_compute_has_data_import')

    @api.constrains("branch_id")
    def _check_default_warehouse(self):
        for record in self:
            if not record.branch_id.warehouse_id:
                raise ValidationError(_("対象の支店にデフォルト倉庫が設定されていません。組織マスタの設定を確認してください。"))

    @api.depends('powernet_sale_record_ids')
    def _compute_has_data_import(self):
        for record in self:
            if record.powernet_sale_record_ids:
                record.has_data_import = True
            else:
                record.has_data_import = False

    @api.constrains("name")
    def _check_name(self):
        for record in self:
            name_unique = self.env['ss_erp.ifdb.powernet.sales.header'].search_count(
                [('name', '=', record.name)])
            if name_unique > 1:
                raise ValidationError(_("ファイルヘッダー名は検索に使用されます。一意にしてください。"))

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
        if not customer_code:
            raise UserError(
                _('直売売上用の顧客コードの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。（powernet.direct.sales.dummy.customer_id）'))

        customer_id = self.env['res.partner'].search([('ref', '=', customer_code)], limit=1)
        if not customer_id:
            raise UserError(
                _('設定している取引先コードは存在しません。'))

        # 2022/06/30 設計書の変更によりの追加
        gas_product_id = self.env['ir.config_parameter'].sudo().get_param('powernet.gas.basic.charge.product_id')
        if not gas_product_id:
            raise UserError(
                _('ガス基本料金のプロダクトIDの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。（powernet.gas.basic.charge.product_id）'))

        gas_product = self.env['product.template'].browse(gas_product_id)
        if not gas_product:
            raise UserError(
                _('設定しているプロダクトIDは、プロダクトマスタに存在しません。プロダクトマスタを確認してください。'))

        exe_data = self.powernet_sale_record_ids.filtered(lambda line: line.status in ('wait', 'error')).sorted(
            key=lambda k: (k['sales_date'], k['customer_code'], k['data_types']))

        # Get list product uom exchange
        powernet_type_ids = self.env['ss_erp.external.system.type'].search([('code', '=', 'power_net')]).mapped('id')
        convert_product_unit_type_ids = self.env['ss_erp.convert.code.type'].search(
            [('code', '=', 'product_unit')]).mapped('id')
        uom_code_convert = self.env['ss_erp.code.convert'].search(
            [('external_system', 'in', powernet_type_ids), ('convert_code_type', 'in', convert_product_unit_type_ids)]).sorted(
                key=lambda k: (k['external_code'], k['priority_conversion']))

        uom_dict = {}
        for uom in uom_code_convert:
            if not uom_dict.get(uom['external_code']):
                uom_dict[uom['external_code']] = uom['internal_code'].id

        product_product_ids = self.env['product.product'].search([]).mapped('id')

        failed_so = []
        success_dict = {}
        for line in exe_data:
            key = str(line.sales_date) + '_' + str(line.customer_code)
            error_message = False
            if int(line.product_code) not in product_product_ids:
                line.status = 'error'
                error_message = '商品コードがプロダクトマスタに存在しません。'

            if not uom_dict.get(line.unit_code):
                line.status = 'error'
                if error_message:
                    error_message += '単位コードの変換に失敗しました。コード変換マスタを確認してください。'
                else:
                    error_message = '単位コードの変換に失敗しました。コード変換マスタを確認してください。'

            if not error_message:
                if key in failed_so:
                    continue
                else:
                    # 2022/06/30 販売伝票を作成する際に、プロダクトIDが上記で取得したガス基本料金のプロダクトIDと一致する場合、数量を「1」で更新する。
                    quantity = 1 if (int(line.product_code) == gas_product_id) else line.quantity
                    order_line = {
                        'product_id': int(line.product_code),
                        'product_uom_qty': quantity,
                        'product_uom': uom_dict[line.unit_code],
                    }

                    # 2022/05/09 Add new client_order_ref
                    client_order_ref = '%s：%s' % (line.customer_code,line.search_remarks_6)

                    if not success_dict.get(key):
                        so = {
                            'x_organization_id': self.branch_id.id,
                            'warehouse_id': self.branch_id.warehouse_id.id,
                            'partner_id': customer_id.id,
                            'partner_invoice_id': customer_id.id,
                            'partner_shipping_id': customer_id.id,
                            'date_order': line.sales_date,
                            'state': 'draft',
                            'x_no_approval_required_flag': True,
                            'order_line': [(0, 0, order_line)],
                            'client_order_ref': client_order_ref,
                        }
                        success_dict[key] = so
                    else:
                        success_dict[key]['order_line'].append((0, 0, order_line))
            else:
                if key not in failed_so:
                    failed_so.append(key)
                if success_dict.get(key, False):
                    success_dict.pop(key, None)
                line.write({
                    'status': 'error',
                    'error_message': error_message
                })

        for key, value in success_dict.items():
            sale_id = self.env['sale.order'].create(value)
            success_dict[key]['sale_id'] = sale_id.id

        success_list = success_dict.keys()
        for line in exe_data:
            key = str(line.sales_date) + '_' + str(line.customer_code)
            if key in success_list:
                line.update({
                    'status': 'success',
                    'sale_id': success_dict[key]['sale_id'],
                    'processing_date': datetime.now(),
                    'error_message': False,
                })


class IFDBPowerNetSalesHeadDetail(models.Model):
    _name = 'ss_erp.ifdb.powernet.sales.detail'
    _description = 'PowerNet詳細'

    powernet_sales_header_id = fields.Many2one('ss_erp.ifdb.powernet.sales.header', 'PowerNetセールスヘッダー',
                                               required=True, ondelete="cascade")
    status = fields.Selection(selection=[
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラー')
    ], string='ステータス', default="wait", required=True)
    processing_date = fields.Datetime('処理日時', index=True)
    customer_code = fields.Char('需要家コード', index=True)
    billing_summary_code = fields.Char('請求まとめコード')
    sales_date = fields.Date('売上日', index=True)
    slip_type = fields.Char('伝票種類')
    slip_no = fields.Char('伝票Ｎｏ')
    data_types = fields.Char('データ種類', index=True)
    cash_classification = fields.Char('現金／掛け区分')
    product_code = fields.Char('商品コード')
    product_code_2 = fields.Char('商品コード 2')
    product_name = fields.Char('商品名')
    product_remarks = fields.Char('商品備考')
    sales_category = fields.Char('売上区分')
    quantity = fields.Float('数量')
    unit_code = fields.Char('単位コード')
    unit_price = fields.Float('単価')
    amount_of_money = fields.Float('金額')
    consumption_tax = fields.Float('消費税')
    sales_amount = fields.Float('売上額')
    quantity_after_conversion = fields.Float('換算後数量')
    search_remarks_1 = fields.Char('検索備考 1')
    search_remarks_2 = fields.Char('検索備考 2')
    search_remarks_3 = fields.Char('検索備考 3')
    search_remarks_4 = fields.Char('検索備考 4')
    search_remarks_5 = fields.Char('検索備考 5')
    search_remarks_6 = fields.Char('検索備考 6')
    search_remarks_7 = fields.Char('検索備考 7')
    search_remarks_8 = fields.Char('検索備考 8')
    search_remarks_9 = fields.Char('検索備考 9')
    search_remarks_10 = fields.Char('検索備考 10')
    sales_classification_code_1 = fields.Char('販売分類コード 1')
    sales_classification_code_2 = fields.Char('販売分類コード 2')
    sales_classification_code_3 = fields.Char('販売分類コード 3')
    consumer_sales_classification_code_1 = fields.Char('需要家販売分類コード 1')
    consumer_sales_classification_code_2 = fields.Char('需要家販売分類コード 2')
    consumer_sales_classification_code_3 = fields.Char('需要家販売分類コード 3')
    consumer_sales_classification_code_4 = fields.Char('需要家販売分類コード 4')
    consumer_sales_classification_code_5 = fields.Char('需要家販売分類コード 5')
    product_classification_code_1 = fields.Char('商品分類コード 1')
    product_classification_code_2 = fields.Char('商品分類コード 2')
    product_classification_code_3 = fields.Char('商品分類コード 3')
    error_message = fields.Char('エラーメッセージ')
    sale_id = fields.Many2one('sale.order', '販売オーダ参照')
