from odoo import models, fields, api, _


class IFDBPropaneSalesHeader(models.Model):
    _name = 'ss_erp.ifdb.propane.sales.header'
    _description = 'Propane sales'

    name = fields.Char(string='Name')
    upload_date = fields.Datetime(
        string='Upload date and time', index=True, required=True)
    user_id = fields.Many2one('res.users', string='Manager')
    branch_id = fields.Many2one('ss_erp.organization', string='Branch')
    status = fields.Selection([
        ('wait', '処理待ち'),
        ('success', '成功'),
        ('error', 'エラーあり'),
    ], string='Status', default='wait', index=True)
    sales_detail_ids = fields.One2many(
        'ss_erp.ifdb.propane.sales.detail', 'propane_sales_header_id',
        string='Propane sales file header')
    
    
    def btn_processing_execution(self):
        return True