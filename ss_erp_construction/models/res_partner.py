from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_construction_account_receivable_id = fields.Many2one(
        comodel_name='account.account',
        string='完成工事勘定',
        required=False)

    x_construction_account_payable_id = fields.Many2one(
        comodel_name='account.account',
        string='工事未払勘定',
        required=False)

