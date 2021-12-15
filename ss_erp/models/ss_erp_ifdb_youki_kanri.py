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
        readonly=True
    )
    youki_kanri_detail_ids = fields.One2many(comodel_name="ss_erp.ifdb.youki.kanri.detail",
                                             inverse_name="ifdb_youki_kanri_id")

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
        customer_branch_code = self.env['ss_erp.ifdb.youki.kanri.detail'].search_read([], ['customer_branch_code'])
        partner_ids = self.env['res.partner'].search([('ref', '=', customer_branch_code)])
        partner_list = []
        for partner in partner_ids:
            if partner['id'] not in partner_list:
                partner_list.append(partner['id'])

        uom_uom_ids = self.env['uom.uom'].search_read([], ['id'])
        uom_list = []
        for uom in uom_uom_ids:
            if uom['id'] not in uom_list:
                uom_list.append(uom['id'])

        product_product_ids = self.env['product.product'].search_read([], ['uom_id'])
        product_list = []
        for product in product_product_ids:
            if product['uom_id'] and product['uom_id'] not in product_list:
                product_list.append(product['uom_id'])

        # Sub-branch C check
        organization_ids = self.env['ss_erp.organization'].search_read([])
        organization_list = []
        for organization_id in organization_ids:
            if organization_id['id'] and organization_id['id'] not in organization_list:
                organization_list.append(organization_id['id'])

        failed_customer_code = []
        success_dict = {}
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
            if line.codeommercial_product_code not in product_list:
                if error_message:
                    error_message += '商商品Ｃがプロダクトマスタに存在しません。'
                else:
                    error_message = '商商品Ｃがプロダクトマスタに存在しません。'
            if line.unit_code not in uom_list:
                if error_message:
                    error_message += '単位Ｃがプロダクト単位マスタに存在しません。'
                else:
                    error_message = '単位Ｃがプロダクト単位マスタに存在しません。'

            if line.customer_business_partner_code not in failed_customer_code:
                if error_message:
                    line.write({
                        'status': 'error',
                        'error_message': error_message
                    })
                    failed_customer_code.append(line.customer_business_partner_code)
                    if success_dict.get(line.sale_ref, False):
                        success_dict.pop(line.sale_ref, None)
                    continue
                else:
                    if not success_dict.get(line.sale_ref):
                        so = {
                            'partner_id': int(line.customer_business_partner_code),
                            'partner_invoice_id': int(line.customer_business_partner_code),
                            'partner_shipping_id': int(line.customer_business_partner_code),
                            'date_order': line.slip_date,
                            'order_line': [(0, 0, {
                                'product_id': int(line.codeommercial_product_code),
                                'product_uom_qty': line.quantity,
                                'product_uom': int(line.unit_code)
                            })],
                        }
                        success_dict[line.sale_ref] = {
                            'order': so,
                            'success': [line.id]
                        }
                    else:
                        order_line = {
                            'product_id': int(line.codeommercial_product_code),
                            'product_uom_qty': line.quantity,
                            'product_uom': int(line.unit_code)
                        }
                        success_dict[line.sale_ref]['order']['order_line'].append(
                            (0, 0, order_line))
                        success_dict[line.sale_ref]['success'].append(line.id)
            else:
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
