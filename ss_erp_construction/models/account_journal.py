from odoo import fields, models, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_construction = fields.Boolean('工事フラグ', default=False)
