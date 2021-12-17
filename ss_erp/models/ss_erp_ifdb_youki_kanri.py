from odoo import models, fields, api
from datetime import datetime


class YoukiKanri(models.Model):
    _name = "ss_erp.ifdb.youki.kanri"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Youki Kanri"

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


    _sql_constraints = [
        (
            "name_uniq",
            "UNIQUE(name)",
            "Name is used for searching, please make it unique!"
        )
    ]

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
        branch_code_convert = self.env['ss_erp.code.convert'].search_read(
            [('external_system', 'in', youki_kanri_type_ids), ('convert_code_type', 'in', convert_branch_type_ids)],
            ['external_code', 'internal_code'])
        branch_dict = {}
        for branch in branch_code_convert:
            if not branch_dict.get(branch['external_code']):
                if branch['external_code']:
                    internal_code = branch['internal_code'].split(",")[1]
                    branch_dict[branch['external_code']] = int(internal_code)
        # convert unit code
        convert_product_unit_ids = self.env['ss_erp.convert.code.type'].search([('code', '=', 'product_unit')]).mapped(
            'id')
        unit_code_convert = self.env['ss_erp.code.convert'].search_read(
            [('external_system', 'in', youki_kanri_type_ids), ('convert_code_type', 'in', convert_product_unit_ids)],
            ['external_code', 'internal_code'])
        uom_dict = {}
        for uom in unit_code_convert:
            if not uom_dict.get(uom['external_code']):
                if uom['external_code']:
                    internal_code = uom['internal_code'].split(",")[1]
                    uom_dict[uom['external_code']] = int(internal_code)
        # Advisor C check
        customer_branch_sub_list = []
        customer_branch_sub_check = self.env['ss_erp.ifdb.youki.kanri.detail'].search_read(
            [('customer_business_partner_code', '!=', False)], ['customer_business_partner_code'])
        for rec in customer_branch_sub_check:
            customer_branch_sub_list.append(rec['customer_business_partner_code'])
        partner_ids = self.env['res.partner'].search([('ref', 'in', customer_branch_sub_list)])
        partner_list = []
        for partner in partner_ids:
            if partner['ref'] not in partner_list:
                partner_list.append(partner['ref'])

        # Commercial product C check
        product_product_ids = self.env['product.product'].search_read([], ['default_code'])
        product_dict = {}
        for product in product_product_ids:
            if product['default_code']:
                product_dict[product['default_code']] = product['id']

        # Sub-branch C check and Commercial branch C check
        organization_ids = self.env['ss_erp.organization'].search_read([], ['organization_code'])
        organization_list = []
        for organization_id in organization_ids:
            if organization_id['organization_code'] and organization_id['organization_code'] not in organization_list:
                organization_list.append(organization_id['organization_code'])

        failed_customer_code = []
        success_dict = {}
        success_po_dict = {}
        for line in exe_data:
            error_message = False
            if line.customer_business_partner_code not in partner_list:
                error_message = '顧取引先Ｃが連絡先マスタに存在しません。'
            if line.customer_branch_code not in organization_list:
                if error_message:
                    error_message += '顧取引先Ｃが連絡先マスタに存在しません。'
                else:
                    error_message = '顧取引先Ｃが連絡先マスタに存在しません。'
            if line.codeommercial_branch_code not in organization_list:
                if error_message:
                    error_message += '商支店Ｃが組織マスタに存在しません。'
                else:
                    error_message = '商支店Ｃが組織マスタに存在しません。'
            if (line.codeommercial_product_code) not in product_dict:
                if error_message:
                    error_message += '商商品Ｃがプロダクトマスタに存在しません。'
                else:
                    error_message = '商商品Ｃがプロダクトマスタに存在しません。'
            if line.unit_code not in uom_dict:
                if error_message:
                    error_message += '単位Ｃがプロダクト単位マスタに存在しません。'
                else:
                    error_message = '単位Ｃがプロダクト単位マスタに存在しません。'

            key = line.slip_processing_classification
            if line.customer_business_partner_code not in failed_customer_code:
                if error_message:
                    line.write({
                        'status': 'error',
                        'error_message': error_message
                    })
                    failed_customer_code.append(line.customer_business_partner_code)

                    if success_dict.get(line.slip_processing_classification, False):
                        success_dict.pop(line.slip_processing_classification, None)
                    continue
                else:
                    if key == '6':
                        if not success_dict.get(key, 0) == 6:
                            so = {
                                'partner_id': int(line.customer_business_partner_code),
                                'partner_invoice_id': int(line.customer_business_partner_code),
                                'partner_shipping_id': int(line.customer_business_partner_code),
                                'date_order': datetime.strptime(line.slip_date, '%Y/%m/%d'),
                                'order_line': [(0, 0, {
                                    'product_id': int(line.codeommercial_product_code),
                                    'product_uom_qty': line.quantity,
                                    'product_uom': int(line.unit_code)
                                })],
                            }
                            success_dict[key] = {
                                'order': so,
                                'success': [line.id]
                            }
                        else:
                            order_line = {
                                'product_id': int(line.codeommercial_product_code),
                                'product_uom_qty': line.quantity,
                                'product_uom': int(line.unit_code)
                            }
                            success_dict[key]['order']['order_line'].append((0, 0, order_line))
                            success_dict[key]['success'].append(line.id)


                    elif key == '7':
                        if not success_po_dict.get(key,0) == 7:
                            po = {
                                'partner_id': int(line.customer_business_partner_code),
                                'date_order': datetime.strptime(line.slip_date,'%Y/%m/%d'),
                                'picking_type_id': self.env.ref('stock.picking_type_in').id,
                                'order_line': [(0, 0, {
                                    'product_id': int(line.codeommercial_product_code),
                                    'product_qty': line.quantity,
                                    'date_planned':datetime.strptime(line.slip_date,'%Y/%m/%d')
                                })],
                            }
                            success_po_dict[key] = {
                                'order': po,
                                'success': [line.id]
                            }
                        else:
                            order_line = {
                                'product_id': int(line.codeommercial_product_code),
                                'product_qty': line.quantity,
                                'date_planned': datetime.strptime(line.slip_date,'%Y/%m/%d')
                            }
                            success_po_dict[key]['order']['order_line'].append((0, 0, order_line))
                            success_po_dict[key]['success'].append(line.id)

            else:
                line.write({
                    'status': 'error',
                    'error_message': error_message
                })
        # CREATE SO
        for key, value in success_dict.items():
            sale_id = self.env['sale.order'].create(value['order'])
            success_dict[key]['sale_id'] = sale_id.id

        # CREATE SOL
        success_list = success_dict.keys()
        for line in exe_data:
            if success_dict.get(key) :
                line.write({
                    'status': 'success',
                    'sale_id': success_dict[line.slip_processing_classification]['sale_id']
                })

        # CREATE PO
        for key, value in success_po_dict.items():
            po_id = self.env['purchase.order'].create(value['order'])
            success_po_dict[key]['po'] = po_id.id

        # CREATE POL
        success_po_list = success_po_dict.keys()
        for line in exe_data:
            if success_po_dict.get(key) :
                line.write({
                    'status': 'success',
                    'purchase_id': success_po_dict[key]['po']
                })


