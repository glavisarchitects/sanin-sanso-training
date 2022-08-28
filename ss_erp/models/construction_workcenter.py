from odoo import fields, models, api


class ConstructionWorkcenter(models.Model):
    _name = 'construction.workcenter'
    _description = '工事作業区'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code desc'

    name = fields.Char('作業区名')
    code = fields.Char('コード')
    costs_hour = fields.Float(string='時間毎の費用')
    note = fields.Text('説明')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True, string="会社")
    active = fields.Boolean(default=True)
