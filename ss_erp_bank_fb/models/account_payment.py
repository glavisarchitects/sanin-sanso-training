from odoo import fields, models, api
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.depends('partner_id', 'company_id', 'payment_type', 'journal_id')
    def _compute_available_partner_bank_ids(self):
        super()._compute_available_partner_bank_ids()
        a005_account_transfer_result_journal_id = self.env['ir.config_parameter'].sudo().get_param(
            'A005_account_transfer_result_journal_id')
        if not a005_account_transfer_result_journal_id:
            raise UserError('仕訳帳情報の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。')

        journal_ids = a005_account_transfer_result_journal_id.split(",")
        if len(journal_ids) != 2:
            raise UserError('仕訳帳情報の設定は間違っています。もう一度ご確認してください。')
        # 当座預金
        journal_account_1121 = journal_ids[0]
        # 普通預金
        journal_account_1122 = journal_ids[1]
        
        for pay in self:
            if pay.payment_type == 'inbound':
                pay.available_partner_bank_ids = pay.journal_id.bank_account_id
            else:
                if pay.journal_id.id == int(journal_ids[0]):
                    pay.available_partner_bank_ids = pay.partner_id.bank_ids.filtered(
                        lambda x: x.acc_type == 'checking')
                elif pay.journal_id.id == int(journal_ids[1]):
                    pay.available_partner_bank_ids = pay.partner_id.bank_ids.filtered(
                        lambda x: x.acc_type == 'bank')
                else:
                    pay.available_partner_bank_ids = pay.partner_id.bank_ids \
                        .filtered(lambda x: x.company_id.id in (False, pay.company_id.id))._origin
