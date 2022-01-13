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

    # HuuPhong 2011/01/11
    partner_id = fields.Many2one('res.partner', 'Account Holder', ondelete='cascade', index=True, required=False,)
    partner_form_id = fields.Many2one('ss_erp.res.partner.form', 'Account Holder', ondelete='cascade', index=True, required=False,)

    @api.constrains('partner_id', 'bank_id', 'x_bank_branch', 'acc_type', 'acc_number')
    def check_bank_account(self):
        for record in self:
            if record.partner_id:
                exist_account = self.search(
                    [('bank_id', '=', record.bank_id.id), ('x_bank_branch', '=', record.x_bank_branch),
                     ('acc_type', '=', record.acc_type), ('acc_number', '=', record.acc_number),
                     ('partner_id', '=', record.partner_id.id)], limit=1)
                if exist_account and exist_account != record:
                    raise ValidationError(_("口座情報は既に登録済みの可能性があります。"))

