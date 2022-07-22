from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.model
    def get_supported_account_types(self):
        return self._get_supported_account_types()

    @api.model
    def _get_supported_account_types(self):
        return [('bank', _('普通')), ('checking', _('当座'))]

    acc_type = fields.Selection(selection=lambda x: x.env['res.partner.bank'].get_supported_account_types(),
                                string='預金種目', default='bank', index=True)
    x_bank_branch = fields.Char(string='支店', index=True)
    x_acc_holder_furigana = fields.Char(string='フリガナ', index=True)

    # HuuPhong 2011/01/11
    partner_id = fields.Many2one('res.partner', 'Account Holder', ondelete='cascade',required=False)
    partner_form_id = fields.Many2one('ss_erp.res.partner.form', 'Account Holder', ondelete='cascade')
    # TuyenTN 2022/07/15
    acc_holder_name = fields.Char(string='口座名義')
    bank_id = fields.Many2one('res.bank', string='銀行')
    organization_id = fields.Many2one('ss_erp.organization',string='Organization')
    x_acc_withdrawal = fields.Boolean(string='引落')
    x_acc_transfer = fields.Boolean(string='振込')

    @api.constrains('bank_id', 'x_bank_branch', 'acc_type', 'acc_number')
    def check_bank_account(self):
        for record in self:
            exist_account = self.search(
                [('bank_id', '=', record.bank_id.id), ('x_bank_branch', '=', record.x_bank_branch),
                 ('acc_type', '=', record.acc_type), ('acc_number', '=', record.acc_number),
                 ], limit=1)
            if exist_account and exist_account != record:
                raise ValidationError(_("申請対象の取引先は、顧客または仕入先として既に登録済みの可能性があります。"))


    @api.model
    def create(self, vals):
        if vals.get('partner_id'):
            partner_form_id = self.env['ss_erp.res.partner.form'].search([('res_partner_id', '=', vals.get('partner_id'))])
            if partner_form_id:
                vals['partner_form_id'] = partner_form_id.id
        return super(ResPartnerBank, self).create(vals)
        # res = super(ResPartnerBank, self).create(vals)
        # if res.partner_id and not res.partner_form_id:
        #     partner_form_id = self.env['ss_erp.res.partner.form'].search(
        #         [('res_partner_id', '=', vals.get('partner_id'))],limit=1)
        #     partner_form_id.update('')
        # return res


