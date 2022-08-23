from odoo import fields, models, api


class ConstructionWorkcenter (models.Model):
    _name = 'construction.workcenter'
    _description = '工事作業区'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('作業区名')
    costs_hour = fields.Float(string='時間毎の費用')
    note = fields.Text('説明')


