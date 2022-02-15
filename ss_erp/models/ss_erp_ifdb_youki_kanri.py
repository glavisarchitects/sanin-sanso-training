from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError


class YoukiKanri(models.Model):
    _name = "ss_erp.ifdb.youki.kanri"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "容器管理ヘッダ"

    name = fields.Char(
        string="名称"
    )
    upload_date = fields.Datetime(
        string="アップロード日時",
        index=True,
        default=fields.Datetime.now()
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="担当者",
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
            ("error", "エラーあり"),
        ],
        string="ステータス",
        required=True,
        default="wait",
        index=True,
        readonly=True,
        compute='_compute_status',
    )
    youki_kanri_detail_ids = fields.One2many(comodel_name="ss_erp.ifdb.youki.kanri.detail",
                                             inverse_name="ifdb_youki_kanri_id")
    has_data_import = fields.Boolean(compute='_compute_has_data_import')

    #
    @api.depends('youki_kanri_detail_ids')
    def _compute_has_data_import(self):
        for record in self:
            if record.youki_kanri_detail_ids:
                record.has_data_import = True
            else:
                record.has_data_import = False

    # _sql_constraints = [
    #     (
    #         "name_uniq",
    #         "UNIQUE(name)",
    #         "Name is used for searching, please make it unique!"
    #     )
    # ]

    @api.constrains("name")
    def _check_name(self):
        for record in self:
            name_unique = self.env['ss_erp.ifdb.youki.kanri'].search_count(
                [('name', '=', record.name)])
            if name_unique > 1:
                raise ValidationError(_("ファイルヘッダー名は検索に使用されます。一意にしてください。"))

    def action_import(self):
        self.ensure_one()
        self.upload_date = fields.Datetime.now()
        return {
            "type": "ir.actions.client",
            "tag": "import",
            "params": {
                "model": "ss_erp.ifdb.youki.kanri.detail",
                "context": {
                    "default_import_file_header_model": self._name,
                    "default_import_file_header_id": self.id,
                },
            }
        }

    @api.depends('youki_kanri_detail_ids.status')
    def _compute_status(self):
        for record in self:
            if record.youki_kanri_detail_ids:
                status_list = record.youki_kanri_detail_ids.mapped('status')
                record.status = "success"
                if "error" in status_list:
                    record.status = "error"
                elif "wait" in status_list:
                    record.status = "wait"
            else:
                record.status = "wait"

    def action_processing_execution(self):
        for r in self:
            r._processing_execution()

    def _processing_execution(self):
        self.ensure_one()
        exe_data = self.youki_kanri_detail_ids.filtered(lambda line: line.status in ('wait', 'error')).sorted(
            key=lambda k: (k['id']))
        # convert branch code
        youki_kanri_type_ids = self.env['ss_erp.external.system.type'].search([('code', '=', 'youki_kanri')]).mapped(
            'id')
        convert_branch_type_ids = self.env['ss_erp.convert.code.type'].search([('code', '=', 'branch')]).mapped('id')
        branch_code_convert = self.env['ss_erp.code.convert'].search(
            [('external_system', 'in', youki_kanri_type_ids), ('convert_code_type', 'in', convert_branch_type_ids)]).sorted(
                key=lambda k: (k['external_code'], k['priority_conversion']))

        branch_dict = {}
        for branch in branch_code_convert:
            if not branch_dict.get(branch['external_code']):
                if branch['external_code']:
                    branch_dict[branch['external_code']] = branch['internal_code'].id

        # convert unit code
        convert_product_unit_ids = self.env['ss_erp.convert.code.type'].search([('code', '=', 'product_unit')]).mapped(
            'id')
        unit_code_convert = self.env['ss_erp.code.convert'].search(
            [('external_system', 'in', youki_kanri_type_ids), ('convert_code_type', 'in', convert_product_unit_ids)])
        uom_dict = {}
        for uom in unit_code_convert:
            if not uom_dict.get(uom['external_code']):
                uom_dict[uom['external_code']] = uom['internal_code'].id

        partner_list = self.env['res.partner'].search([]).mapped('id')
        product_list = self.env['product.product'].search([]).mapped('id')
        organization_list = self.env['ss_erp.organization'].search([]).mapped('id')

        fail_list = []
        so_dict = {}
        po_dict = {}
        inventoryorder_dict = {}
        for line in exe_data:
            error_message = False
            if int(line.customer_business_partner_code) not in partner_list:
                error_message = '顧取引先Ｃが連絡先マスタに存在しません。'

            if int(line.customer_branch_code) not in organization_list:
                if error_message:
                    error_message += '顧取引先Ｃが連絡先マスタに存在しません。'
                else:
                    error_message = '顧取引先Ｃが連絡先マスタに存在しません。'

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

            if not uom_dict.get(line.unit_code):
                if error_message:
                    error_message += '単位Ｃがプロダクト単位マスタに存在しません。'
                else:
                    error_message = '単位Ｃがプロダクト単位マスタに存在しません。'

            key = str(line.slip_processing_classification) + '_' + str(line.slip_date) + '_' + str(
                line.codeommercial_branch_code) + '_' + str(line.customer_business_partner_code)

            if key not in fail_list:
                if error_message:
                    line.write({
                        'status': 'error',
                        'error_message': error_message
                    })
                    fail_list.append(key)
                    if so_dict.get(key, False):
                        so_dict.pop(key, None)
                    if po_dict.get(key, False):
                        po_dict.pop(key, None)
                    if inventoryorder_dict.get(key, False):
                        inventoryorder_dict.pop(key, None)
                    continue
                else:
                    if line.slip_processing_classification == '6' or line.slip_processing_classification == 'A':
                        order_line = {
                            'product_id': int(line.codeommercial_product_code),
                            'product_uom_qty': line.quantity if line.slip_processing_classification == '6' else 1,
                            'product_uom': uom_dict.get(line.unit_code)
                        }
                        if not so_dict.get(key, 0):
                            so = {
                                'x_organization_id':int(line.codeommercial_branch_code),
                                'partner_id': int(line.customer_business_partner_code),
                                'partner_invoice_id': int(line.customer_business_partner_code),
                                'partner_shipping_id': int(line.customer_business_partner_code),
                                'date_order': datetime.strptime(line.slip_date, '%Y/%m/%d'),
                                'state':'draft',
                                'x_no_approval_required_flag': True,
                                'order_line': [(0, 0, order_line)],
                            }
                            so_dict[key] = {
                                'order': so,
                            }
                        else:
                            so_dict[key]['order']['order_line'].append((0, 0, order_line))
                    elif line.slip_processing_classification == '7':
                        order_line = {
                            'product_id': int(line.codeommercial_product_code),
                            'product_qty': line.quantity,
                            'product_uom': line.unit_code,
                            'date_planned': datetime.strptime(line.slip_date, '%Y/%m/%d')
                        }
                        if not po_dict.get(key, 0):
                            po = {
                                'partner_id': int(line.customer_business_partner_code),
                                'date_order': datetime.strptime(line.slip_date, '%Y/%m/%d'),
                                'picking_type_id': self.env.ref('stock.picking_type_in').id,
                                'order_line': [(0, 0, order_line)],
                            }
                            po_dict[key] = {
                                'order': po,
                            }
                        else:
                            po_dict[key]['order']['order_line'].append((0, 0, order_line))

                    elif line.slip_processing_classification == '9':
                        order_line = {
                            'product_id': int(line.codeommercial_product_code),
                            'product_uom_qty': float(line.quantity),
                            'product_uom': uom_dict.get(line.unit_code)
                        }
                        if not inventoryorder_dict.get(key, 0):
                            inv_order = {
                                'organization_id': int(line.codeommercial_branch_code),
                                'state': 'draft',
                                'scheduled_date': datetime.strptime(line.slip_date, '%Y/%m/%d'),
                                'inventory_order_line_ids': [(0, 0, order_line)],
                            }
                            inventoryorder_dict[key] = {
                                'order': inv_order,
                            }
                        else:
                            inventoryorder_dict[key]['order']['inventory_order_line_ids'].append((0, 0, order_line))
            else:
                line.write({
                    'status': 'error',
                    'error_message': error_message
                })
        # CREATE SO

        for key, value in so_dict.items():
            sale_id = self.env['sale.order'].create(value['order'])
            so_dict[key]['sale_id'] = sale_id.id

        # CREATE PO
        for key, value in po_dict.items():
            po_id = self.env['purchase.order'].create(value['order'])
            po_dict[key]['po_id'] = po_id.id

        # CREATE INVENTORY ORDER
        for key, value in inventoryorder_dict.items():
            inventory_order_id = self.env['ss_erp.inventory.order'].create(value['order'])
            inventoryorder_dict[key]['inv_order_id'] = inventory_order_id.id

        for line in exe_data:
            key = str(line.slip_processing_classification) + '_' + str(line.slip_date) + '_' + str(
                line.codeommercial_branch_code) + '_' + str(line.customer_business_partner_code)
            if so_dict.get(key):
                line.write({
                    'status': 'success',
                    'processing_date':datetime.now(),
                    'sale_id': so_dict[key]['sale_id']
                })
            if po_dict.get(key):
                line.write({
                    'status': 'success',
                    'processing_date': datetime.now(),
                    'purchase_id': po_dict[key]['po_id']
                })
            if inventoryorder_dict.get(key):
                line.write({
                    'status': 'success',
                    'processing_date': datetime.now(),
                    'inventory_order_id': inventoryorder_dict[key]['inv_order_id']
                })
