from odoo import fields, models, api


class BankCommission (models.Model):
    _name = 'ss_erp.bank.commission'
    _description = '振込手数料'
    _rec_name = 'bank_id'

    # name = fields.Char()
    bank_id = fields.Many2one(
        comodel_name='res.bank',
        string='振込利用銀行',
        required=False)
    # netbanking_service = fields.Char(
    #     string='利用サービス',
    #     required=False)

    paid_amount = fields.Monetary(store=True, string='振込金額')
    range = fields.Selection(
        string='範囲',
        selection=[('up', '以上'),
                   ('down','未満'),
                   ('equal', '同じ'), ],
        required=False, )
    our_bank = fields.Monetary(store=True, string='当行あて手数料')
    other_bank = fields.Monetary(store=True, string='他行あて手数料')
    memo = fields.Char(string='メモ')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id.id, readonly=1)
