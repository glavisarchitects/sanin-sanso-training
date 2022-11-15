from odoo import fields, models, api


class ConstructionCategory(models.Model):
    _name = 'ss_erp.construction.category'
    _description = '工事種別'

    name = fields.Char(string="工事種別")
    memo = fields.Char("備考")
    user_id = fields.Many2one(
        comodel_name='res.users', default=lambda self: self.env.uid)