from odoo import fields, models, api
import base64
from odoo.exceptions import UserError


def get_multi_character(n, key=' '):
    return key * n

class AccountPaymentWizard(models.TransientModel):
    _name = 'zengin.remittance.receipt.notification'
    _description = 'Zengin 送金受領通知データと領収書の照合'

    from_date = fields.Date(string="有効開始日", copy=False)
    to_date = fields.Date(string="有効終了日", copy=False,)
    transfer_date = fields.Date(string='振込日')







