from odoo import models, fields, api

PAYMENT_METHOD = [
    ('cash', '現金'),
    ('check', '小切手'),
    ('transfer', '振込'),
    ('bills', '手形'),
    ('offset', '相殺'),
]


class PartnerPaymentTerm(models.Model):
    _name = 'ss_erp.partner.payment.term'
    _description = 'Customer Transaction Terms'

    name = fields.Char(string='Name')
    more_than_amount = fields.Float(string='Amount of 10,000 yen or more')
    more_than_deadline = fields.Char(
        string='Closing date of 10,000 yen or more')
    more_than_payment_site = fields.Char(
        string='Payment site for 10,000 yen or more')
    more_than_payment_method = fields.Selection(PAYMENT_METHOD,
        string='Payment method of 10,000 yen or more', default='transfer')
    less_than_amount = fields.Float(string='Amount of less than 10,000 yen')
    less_than_deadline = fields.Char(
        string='Closing date of 10,000 yen or less')
    less_than_payment_site = fields.Char(
        string='Payment site for 10,000 yen or less')
    less_than_payment_method = fields.Selection(PAYMENT_METHOD,
        string='Payment method of 10,000 yen or less', default='transfer')
    collecting_money = fields.Selection([
        ('yes', '有'),
        ('no', '無'),
    ], string='Collecting money', default='no')
    fee_burden = fields.Selection([
        ('other_side', '先方'),
        ('our_side', '当方'),
    ], string='Fee burden', default='our_side')
    bill_site = fields.Char(string='Bill site')
    partner_id = fields.Many2one('res.partner', 'Contact address')
