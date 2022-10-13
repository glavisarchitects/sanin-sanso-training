from odoo import fields, models, api
import base64
from odoo.exceptions import UserError


def get_multi_character(n, key=' '):
    return key * n


class AccountMoveWizard(models.TransientModel):
    _name = 'zengin.account.transfer.request.fb'
    _description = '全銀は口座振替が必要 FB作成'

    fb_start_date = fields.Date(string="有効開始日", copy=False)
    fb_end_date = fields.Date(string="有効終了日", copy=False, )
    transfer_date = fields.Date(string='引落日')

    @api.onchange('fb_start_date', 'fb_end_date')
    def _onchange_from_to__date(self):
        if self.fb_start_date and self.fb_end_date:
            if self.fb_start_date > self.fb_end_date:
                raise UserError('有効開始日は、有効終了日より先の日付は選択できません。"')

    def zengin_account_transfer_request_fb(self):

        organization_user = self.env.user.employee_id.organization_first.id
        domain = [('move_type', '=', 'out_invoice'), ('x_organization_id', '=', organization_user),
                  ('x_receipt_type', '=', 'transfer'), ('x_is_fb_created', '=', False),('x_is_not_create_fb', '=', True),
                  ('invoice_date', '<=', self.fb_end_date), ('invoice_date', '>=', self.fb_start_date),
                  ('state', '=', 'posted'), ('payment_state', '=', 'not_paid')]
        invoice_zengin_data = self.env['account.move'].search(domain)
        if not invoice_zengin_data:
            raise UserError('有効なデータが見つかりません。')

        transfer_requester_code = self.env['ir.config_parameter'].sudo().get_param('transfer_requester_code')
        if not transfer_requester_code:
            raise UserError('山陰酸素工業の依頼人コードを入力してください。')
        if len(transfer_requester_code) != 10:
            raise UserError('山陰酸素工業の依頼人コード長が一致しません')

        company_name = 'ｻﾝｲﾝｻﾝｿｺｳｷﾞｮｳｶﾌﾞｼｷｶﾞｲｼｬ'
        transfer_date_month = self.transfer_date.strftime('%m%d')
        #
        # # TODO: Re confirm Bic bank of which branch?
        head_office_organization = self.env['ss_erp.organization'].search([('organization_code', '=', '00000')],
                                                                          limit=1)
        if not head_office_organization:
            raise UserError('本社支店情報設定してください')

        if not head_office_organization.bank_ids:
            raise UserError('本社支店の銀行を設定してください')

        partner_bank = head_office_organization.bank_ids[0]

        bic_bank_organization = partner_bank.bank_id.bic
        if len(bic_bank_organization) != 4:
            raise UserError('振込先金融機関コード長が一致しません')

        branch_number = partner_bank.x_bank_branch_number
        if len(branch_number) != 3:
            raise UserError('支店番号長が一致しません')
        acc_type = '1' if partner_bank.acc_type == 'bank' else '2'
        acc_number = partner_bank.acc_number  # 7 number from res.partner.bank
        if len(acc_number) != 7:
            raise UserError('口座番号致しません')
        # # header
        file_data = "1910" + transfer_requester_code + company_name + get_multi_character(40 - len(company_name)) + \
                    transfer_date_month + bic_bank_organization + get_multi_character(15) + branch_number + \
                    get_multi_character(15) + acc_type + acc_number + get_multi_character(
            17) + '\r\n'  # '\n\r' = CRLF ?
        # # data

        not_setting_bank_partner = []
        for inv in invoice_zengin_data:
            if not inv.partner_id.bank_ids:
                not_setting_bank_partner.append(inv.partner_id.name)

        if len(not_setting_bank_partner) > 0:
            raise UserError('取引先【%s】の銀行を設定してください' % '、'.join(not_setting_bank_partner))

        total_sum_amount = 0
        bank_list = []
        count=0
        for inv in invoice_zengin_data:
            partner_bic_number = inv.partner_id.bank_ids[0].bank_id.bic
            if len(partner_bic_number) != 4:
                raise UserError('振込先金融機関コード長が一致しません')

            partner_branch_number = inv.partner_id.bank_ids[0].x_bank_branch_number
            if not partner_branch_number:
                raise UserError('振込先金融機関コードまだ設定されていません')
            if len(partner_branch_number) != 3:
                raise UserError('振込先金融機関コード長が一致しません')

            partner_bank_acc_type = '1' if inv.partner_id.bank_ids[0].acc_type == 'bank' else '2'

            partner_acc_number = inv.partner_id.bank_ids[0].acc_number

            if len(partner_acc_number) != 7:
                raise UserError('口座番号長が一致しません')

            partner_acc_holder_furigana = inv.partner_id.bank_ids[0].x_acc_holder_furigana
            if not partner_acc_holder_furigana:
                raise UserError('銀行口座 フリガナ まだ設定されていません')
            # partner_bank_amount = str(int(inv.amount_total))

            if (inv.partner_id.id, inv.partner_id.bank_ids[0].acc_number) not in bank_list:
                bank_list.append((inv.partner_id.id, inv.partner_id.bank_ids[0].acc_number))
            else:
                continue


            # total_amount_line = int(pay.amount)
            partner_bank_amount = int(sum(invoice_zengin_data.filtered(lambda line: line.partner_id.id == inv.partner_id.id and
                                                                                  line.partner_id.bank_ids[0].acc_number == inv.partner_id.bank_ids[0].acc_number
                                                             ).mapped('amount_total')))

            total_sum_amount += partner_bank_amount
            partner_bank_amount = str(partner_bank_amount)

            file_data += '2' + partner_bic_number + get_multi_character(15) + partner_branch_number + \
                         get_multi_character(15) + get_multi_character(4, '0') + partner_bank_acc_type + \
                         partner_acc_number + partner_acc_holder_furigana + \
                         get_multi_character(30 - len(partner_acc_holder_furigana)) + \
                         get_multi_character(10 - len(partner_bank_amount), '0') + partner_bank_amount + \
                         '0' + get_multi_character(20) + '0' + get_multi_character(8) + '\r\n'
            #
            #     # Todo: Now comment this line to test data
            count+=1

        invoice_zengin_data.update({'x_is_fb_created':True})

        # trailer record
        len_line_record = str(count)
        len_total_amount = len(str(total_sum_amount))
        file_data += '8' + get_multi_character(6 - len(len_line_record), '0') + len_line_record + \
                     get_multi_character(12 - len_total_amount, '0') + str(total_sum_amount) + \
                     get_multi_character(6, '0') + get_multi_character(12, '0') + \
                     get_multi_character(6, '0') + get_multi_character(12, '0') + \
                     get_multi_character(65) + '\r\n'
        #
        # # end record
        file_data += '9' + get_multi_character(119)
        # b = bytes(file_data, 'shift-jis')
        b = file_data.encode('shift-jis')
        vals = {
            'name': 'furikae' '.txt',
            'datas': base64.b64encode(b).decode('shift-jis'),
            'type': 'binary',
            'res_model': 'ir.ui.view',
            'res_id': False,
        }
        #
        file_txt = self.env['ir.attachment'].create(vals)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_txt.id) + '?download=true',
            'target': 'new',
        }
