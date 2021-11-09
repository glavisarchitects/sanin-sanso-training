from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.model
    def get_supported_account_types(self):
        return self._get_supported_account_types()

    @api.model
    def _get_supported_account_types(self):
        return [('bank', _('Normal')), ('checking', _('For the time being'))]

    acc_type = fields.Selection(selection=lambda x: x.env['res.partner.bank'].get_supported_account_types(), string='Type', default='bank', required=True, index=True)
    x_bank_branch = fields.Char(string='Branch', required=True, index=True)
    x_acc_holder_furigana = fields.Char(string='Furigana', index=True)
