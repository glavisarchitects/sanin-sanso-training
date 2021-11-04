from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.model
    def _get_supported_account_types(self):
        res = super(ResPartnerBank, self)._get_supported_account_types()
        res.append(('checking', _('For the time being')))
        return res

    x_bank_branch = fields.Char(string='Branch', required=True, index=True)
    x_acc_holder_furigana = fields.Char(string='Furigana', index=True)
