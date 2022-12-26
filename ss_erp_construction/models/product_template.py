from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_construction_account_income_id = fields.Many2one(
        comodel_name='account.account',
        string='工事収益勘定',
        required=False)

    x_construction_account_expense_id = fields.Many2one(
        comodel_name='account.account',
        string='工事費用勘定',
        required=False)

    def _get_product_accounts(self):
        rec = super()._get_product_accounts()
        rec.update({
            'construction_income': self.x_construction_account_income_id,
            'construction_expense': self.x_construction_account_expense_id,
        })
        return rec
