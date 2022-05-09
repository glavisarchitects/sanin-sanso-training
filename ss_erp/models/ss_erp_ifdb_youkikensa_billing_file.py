# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError


class YoukiKensaBilling(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'ss_erp.ifdb.youkikensa.billing.file.header'
    _description = '容器検査'

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
    ], string='ステータス', default='wait', index=True,store=True,compute='_compute_status')

    youki_kensa_detail_ids = fields.One2many('ss_erp.ifdb.youkikensa.billing.file.detail',
                                             'youkikensa_billing_file_header_id')
    has_data_import = fields.Boolean(compute='_compute_has_data_import')

    #
    @api.depends('youki_kensa_detail_ids')
    def _compute_has_data_import(self):
        for record in self:
            if record.youki_kensa_detail_ids:
                record.has_data_import = True
            else:
                record.has_data_import = False

    @api.constrains("name")
    def _check_name(self):
        for record in self:
            name_unique = self.env['ss_erp.ifdb.youkikensa.billing.file.header'].search_count(
                [('name', '=', record.name)])
            if name_unique > 1:
                raise ValidationError(_("ファイルヘッダー名は検索に使用されます。一意にしてください。"))



    @api.depends('youki_kensa_detail_ids.status')
    def _compute_status(self):
        for record in self:
            if record.youki_kensa_detail_ids:
                status_list = record.youki_kensa_detail_ids.mapped('status')
                record.status = "success"
                if "error" in status_list:
                    record.status = "error"
                elif "wait" in status_list:
                    record.status = "wait"
            else:
                record.status = "wait"

    def action_processing_execution(self):
        for r in self:
            r._processing_excution()

    def _processing_excution(self):
        self.ensure_one()

        supplier_code = self.env['ir.config_parameter'].sudo().get_param('container.inspection.center.supplier_id')
        if not supplier_code:
            raise UserError(
                _('仕入先コードの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。（container.inspection.center.supplier_id）'))

        supplier_id = self.env['res.partner'].search([('ref', '=', supplier_code)], limit=1)
        if not supplier_id:
            raise UserError(
                _('設定している仕入先コードは存在しません。'))

        exe_data = self.youki_kensa_detail_ids.filtered(
            lambda line: line.status in ('wait', 'error') and line.product_code and not line.field_3).sorted(
            key=lambda k: (k['sales_date'], k['billing_code']))

        youki_kensa_type_ids = self.env['ss_erp.external.system.type'].search([('code', '=', 'youki_kensa')]).mapped(
            'id')
        product_code_type_ids = self.env['ss_erp.convert.code.type'].search([('code', '=', 'product')]).mapped('id')
        product_code_convert = self.env['ss_erp.code.convert'].search(
            [('external_system', 'in', youki_kensa_type_ids),
             ('convert_code_type', 'in', product_code_type_ids)]).sorted(
            key=lambda k: (k['external_code'], k['priority_conversion'],))

        product_dict = {}
        for product in product_code_convert:
            if not product_dict.get(product['external_code']):
                product_dict[product['external_code']] = product['internal_code'].id

        failed_purchase_orders = []
        success_dict = {}
        for line in exe_data:
            error_message = False
            key = str(line.sales_date) + '_' + line.customer_code
            if not product_dict.get(line.product_code):
                error_message = '商品コードの変換に失敗しました。コード変換マスタを確認してください。'

            if key not in failed_purchase_orders:
                if error_message:
                    line.write({
                        'status': 'error',
                        'error_message': error_message
                    })
                    failed_purchase_orders.append(key)
                    if success_dict.get(key, False):
                        success_dict.pop(key, None)
                    continue
                else:
                    if not success_dict.get(key):
                        po = {
                            'partner_id': supplier_id.id,
                            'date_order': line.sales_date,
                            'picking_type_id': self.env.ref('stock.picking_type_in').id,
                            'order_line': [(0, 0, {
                                'product_id': product_dict[line.product_code],
                                'product_qty': line.return_quantity_for_sale,
                                'date_planned':line.sales_date
                            })],
                        }
                        success_dict[key] = {
                            'order': po,
                        }
                    else:
                        order_line = {
                            'product_id': product_dict[line.product_code],
                            'product_qty': line.return_quantity_for_sale,
                            'date_planned': line.sales_date
                        }
                        success_dict[key]['order']['order_line'].append(
                            (0, 0, order_line))
            else:
                line.write({
                    'status': 'error',
                    'error_message': error_message
                })

        for key, value in success_dict.items():
            po_id = self.env['purchase.order'].create(value['order'])
            success_dict[key]['po'] = po_id.id

        for line in exe_data:
            key = str(line.sales_date) + '_' + line.customer_code
            if success_dict.get(key):
                line.write({
                    'status': 'success',
                    'purchase_id': success_dict[key]['po'],
                    'processing_date':datetime.now(),
                    'error_message': False
                })

    def action_import(self):
        self.ensure_one()
        self.upload_date = fields.Datetime.now()
        return {
            "type": "ir.actions.client",
            "tag": "import",
            "params": {
                "model": "ss_erp.ifdb.youkikensa.billing.file.detail",
                "context": {
                    "default_import_file_header_model": self._name,
                    "default_import_file_header_id": self.id,
                },
            }
        }



class YoukiKensaDetail(models.Model):
    _name = 'ss_erp.ifdb.youkikensa.billing.file.detail'
    _description = 'Youki Kensa Detail'

    youkikensa_billing_file_header_id = fields.Many2one(
        'ss_erp.ifdb.youkikensa.billing.file.header',
        ondelete="cascade"
    )
    status = fields.Selection([
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり'),
    ], string='ステータス', default='wait', index=True)

    processing_date = fields.Datetime('処理日時')
    sales_date = fields.Datetime('売上日付')
    slip_no = fields.Char('伝票No')
    field_3 = fields.Char('フィールド3')
    billing_code = fields.Char('請求先コード')
    billing_abbreviation = fields.Char('請求先略称')
    customer_code = fields.Char('顧客コード')
    customer_abbreviation = fields.Char('得意先略称')
    product_code = fields.Char('商品コード')
    product_name = fields.Char('商品名')
    unit_price = fields.Char('単価')
    return_quantity_for_sale = fields.Char('販売返品数量')
    net_sales_excluding_tax = fields.Char('税抜純売上高')
    consumption_tax = fields.Char('消費税')
    remarks = fields.Char('備考')
    unit_cost = fields.Char('単位原価')
    description = fields.Char('摘要')
    error_message = fields.Char('エラーメッセージ')
    purchase_id = fields.Many2one('purchase.order', '購買オーダ参照')
