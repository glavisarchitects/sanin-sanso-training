from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.model
    def get_supported_account_types(self):
        return self._get_supported_account_types()

    @api.model
    def _get_supported_account_types(self):
        return [('bank', _('Normal')), ('checking', _('For the time being'))]

    acc_type = fields.Selection(selection=lambda x: x.env['res.partner.bank'].get_supported_account_types(),
                                string='Type', default='bank', required=True, index=True)
    x_bank_branch = fields.Char(string='Branch', required=True, index=True)
    x_acc_holder_furigana = fields.Char(string='Furigana', index=True)

    @api.constrains('partner_id', 'bank_id', 'x_bank_branch', 'acc_type', 'acc_number')
    def check_bank_acocunt(self):
        for record in self:
            exist_account = self.search(
                [('bank_id', '=', record.bank_id.id), ('x_bank_branch', '=', record.x_bank_branch),
                 ('acc_type', '=', record.acc_type), ('acc_number', '=', record.acc_number),
                 ('partner_id', '!=', record.partner_id)], limit=1)
            if exist_account:
                raise ValidationError(_("口座情報は既に登録済みの可能性があります。"))

