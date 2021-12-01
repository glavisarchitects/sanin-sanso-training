# -*- coding: utf-8 -*-
from odoo import models, fields, api


class IFDBPowerNetSalesHeader(models.Model):
    _name = 'ss_erp.ifdb.powernet.sales.header'
    _description = 'IFDB PowerNet Sales Header'

    upload_date = fields.Datetime('Upload date and time', index=True)
    name = fields.Char('Name')
    user_id = fields.Many2one('res.users', 'Person in charge', index=True)
    branch_id = fields.Many2one('ss_erp.organization','Branch', index=True)
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



    def processing_execution(self):
        pass
