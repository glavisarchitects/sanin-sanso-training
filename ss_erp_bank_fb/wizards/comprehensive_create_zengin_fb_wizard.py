from odoo import fields, models, api
import base64
from odoo.exceptions import UserError


def get_multi_character(n, key=' '):
    return key * n


class AccountPaymentWizard(models.TransientModel):
    _name = 'comprehensive.create.zengin.fb'
    _description = 'Comprehensive Create Zengin FB Wizard'

    from_date = fields.Date(copy=False)
    to_date = fields.Date(copy=False)
    transfer_date = fields.Date(string='振込日')
    property_supplier_payment_term_id = fields.Many2one('account.payment.term', string='支払条件')

    @api.onchange('from_date', 'to_date')
    def _onchange_from_to__date(self):
        if self.from_date and self.to_date:
            if self.from_date > self.to_date:
                raise UserError('有効開始日は有効終了日より大きくすることはできません。')

    def zengin_general_transfer_fb(self):
        # account_journal = self.env['account.journal']
        partner_match_payment_term = self.env['res.partner'].search(
            [('property_payment_term_id', '=', self.property_supplier_payment_term_id.id), ])
        domain = [('payment_type', '=', 'outbound'), ('x_is_fb_created', '=', False),
                  ('date', '<=', self.to_date), ('date', '>=', self.from_date),
                  ('partner_id', 'in', partner_match_payment_term.ids),
                  ('x_payment_type', '=', 'bank')]
        payment_zengin_data = self.env['account.payment'].search(domain)
        if not payment_zengin_data:
            raise UserError('有効なデータが見つかりません。')

        transfer_requester_code = self.env['ir.config_parameter'].sudo().get_param('transfer_requester_code')
        if not transfer_requester_code:
            raise UserError('山陰酸素工業の依頼人コードを入力してください。')
        if len(transfer_requester_code) != 10:
            raise UserError('山陰酸素工業の依頼人コード長が一致しません')
        # f = open("sample.txt", "w+")
        # f.write("1210" + transfer_requester_code + "ｻﾝｲﾝｻﾝｿｺｳｷﾞｮｳｶﾌﾞｼｷｶﾞｲｼｬ")
        # f.close()
        # f = open("sample.txt", "r")
        company_name = 'ｻﾝｲﾝｻﾝｿｺｳｷﾞｮｳｶﾌﾞｼｷｶﾞｲｼｬ'
        transfer_date_month = self.transfer_date.strftime('%m%d')

        # TODO: Re confirm Bic bank of head office branch
        head_office_organization = self.env['ss_erp.organization'].search([('organization_code', '=', '00000')], limit=1)
        if not head_office_organization:
            raise UserError('本社支店情報設定してください')

        organization_bank = head_office_organization.bank_ids[0]
        if not organization_bank:
            raise UserError('本社支店の銀行を設定してください')

        bic_bank_organization = organization_bank.bank_id.bic
        if len(bic_bank_organization) != 4:
            raise UserError('振込先金融機関コード長が一致しません')

        branch_number = organization_bank.x_bank_branch_number
        if len(branch_number) != 3:
            raise UserError('支店番号長が一致しません')

        acc_type = '1' if organization_bank.acc_type == 'bank' else '2'
        acc_number = organization_bank.acc_number  # 7 number from res.partner.bank
        if len(acc_number) != 7:
            raise UserError('口座番号致しません')

        # header
        file_data = "1210" + transfer_requester_code + company_name + get_multi_character(40 - len(company_name)) + \
                    transfer_date_month + bic_bank_organization + get_multi_character(15) + branch_number + \
                    get_multi_character(15) + acc_type + acc_number + get_multi_character(
            17) + '\r\n'  # '\n\r' = CRLF ?
        # data
        total_sum_amount = 0
        for pay in payment_zengin_data:
            partner_bic_number = pay.partner_bank_id.bank_id.bic
            if len(partner_bic_number) != 4:
                raise UserError('振込先金融機関コード長が一致しません')

            partner_branch_number = pay.partner_bank_id.x_bank_branch_number
            if not partner_branch_number:
                raise UserError('振込先金融機関コードまだ設定されていません')
            if len(partner_branch_number) != 3:
                raise UserError('振込先金融機関コード長が一致しません')

            partner_bank_acc_type = '1' if pay.partner_bank_id.acc_type == 'bank' else '2'

            partner_acc_number = pay.partner_bank_id.acc_number
            if len(partner_acc_number) != 7:
                raise UserError('口座番号長が一致しません')

            partner_acc_holder_furigana = pay.partner_bank_id.x_acc_holder_furigana

            total_amount_line = int(pay.amount)


            # new design total amount = total amount - fee in bank.commission
            if pay.partner_id.x_fee_burden_paid == 'other_side_paid':
                bank_commission = self.env['ss_erp.bank.commission'].search(
                    [('bank_id', '=', organization_bank.bank_id.id)])
                suitable_bank = False
                if bank_commission:
                    for bc in bank_commission:
                        if bc.range == 'up' and total_amount_line > bc.paid_amount:
                            suitable_bank = bc
                            break
                        elif bc.range == 'down' and total_amount_line < bc.paid_amount:
                            suitable_bank = bc
                            break
                        elif bc.range == 'equal' and total_amount_line == bc.paid_amount:
                            suitable_bank = bc
                            break
                if not bank_commission or not suitable_bank:
                    raise UserError('一致する手数料銀行が見つかりません')
                if bic_bank_organization == pay.partner_bank_id.bank_id.bic:
                    total_amount_line = total_amount_line - int(suitable_bank.our_bank)
                else:
                    total_amount_line = total_amount_line - int(suitable_bank.other_bank)

            partner_bank_amount = str(total_amount_line)
            total_sum_amount += int(total_amount_line)
            file_data += '2' + partner_bic_number + get_multi_character(15) + partner_branch_number + \
                         get_multi_character(15) + get_multi_character(4, '0') + partner_bank_acc_type + \
                         partner_acc_number + partner_acc_holder_furigana + \
                         get_multi_character(30 - len(partner_acc_holder_furigana)) + \
                         get_multi_character(10 - len(partner_bank_amount), '0') + partner_bank_amount + '0' + \
                         get_multi_character(10, '0') + get_multi_character(10, '0') + '7' + get_multi_character(
                8) + '\r\n'

            # Todo: Now comment this line to test data
            pay.x_is_fb_created = True
        # trailer record
        len_line_record = str(len(payment_zengin_data))

        len_total_amount = len(str(total_sum_amount))
        file_data += '8' + get_multi_character(6 - len(len_line_record), '0') + len_line_record + \
                     get_multi_character(12 - len_total_amount, '0') + str(total_sum_amount) + get_multi_character(
            101) + '\r\n'

        # end record
        file_data += '9' + get_multi_character(119)
        # b = bytes(file_data, 'shift-jis')
        b = file_data.encode('shift-jis')
        vals = {
            'name': 'sample' '.txt',
            'datas': base64.b64encode(b).decode('shift-jis'),
            'type': 'binary',
            'res_model': 'ir.ui.view',
            'res_id': False,
        }

        file_txt = self.env['ir.attachment'].create(vals)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_txt.id) + '?download=true',
            'target': 'new',
        }

        # pass
