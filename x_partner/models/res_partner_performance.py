from odoo import fields, models


class PartnerPerformance(models.Model):
    _name = "x.partner.sales.information"
    _description = "Partner Performance"

    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Contact", domain="[('company_type', '=', 'company')]",
        readonly=True, copy=False, ondelete="cascade"
    )
    fiscal_year = fields.Char(string="決算期", default=str(fields.Date.today().year))
    amount_of_sale = fields.Char(string="売上高")
    management_profit = fields.Char(string="経営利益")
