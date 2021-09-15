from odoo import fields, models


class ResPartnerBank(models.Model):
    _name = "res.partner.bank"
    _inherit = ["res.partner.bank", "x.x_company_organization.org_mixin"]

    x_deposit_type = fields.Selection(
        selection=[('usually', '普通'), ('current', '当座')],
        string='預金種目')
    x_furigana = fields.Char(string='フリガナ')
    x_branch_name = fields.Char(string='支店名')
    furigana_accname = fields.Char(string='フリガナ', )
