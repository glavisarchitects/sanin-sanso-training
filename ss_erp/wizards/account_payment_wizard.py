from odoo import fields, models


class AccountPaymentWizard(models.TransientModel):

    _name = 'account.payment.wizard'
    _description = 'Account Payment Wizard'

    from_date = fields.Date(string="有効開始日", copy=False)
    to_date = fields.Date(string="有効終了日", copy=False,
                                  default=lambda self: fields.Date.today().replace(month=12, day=31, year=2099))
    transfer_date = fields.Date(string='振込日')

    def zengin_general_transfer_fb(self):
        # account_journal = self.env['account.journal']
        # domain = [('journal_id','=',account_journal.id),
        #           ('payment_type', '=', 'outbound'),('is_fb_created','=',False),
        #           ('date','<=',self.to_date),('date','>=',self.from_date),
        #           ('type','=','bank')
        #           ]
        # zengin_data = self.env['account.payment'].search([domain])
        pass