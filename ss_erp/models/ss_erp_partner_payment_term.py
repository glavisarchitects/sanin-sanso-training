from odoo import models, fields, api

PAYMENT_METHOD = [
    ('hq_transfer', '本社支払(振込)'),
    ('hq_bills', '本社支払(手形)'),
    ('branch_transfer', '支店支払(振込)'),
    ('branch_cash', '支店支払(現金)'),
]


class PartnerPaymentTerm(models.Model):
    _name = 'ss_erp.partner.payment.term'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '取引条件'

    name = fields.Char(string='名称')
    more_than_amount = fields.Float(string='万円以上金額')
    more_than_deadline = fields.Char(
        string='万円以上の締日')
    more_than_payment_site = fields.Char(
        string='万円以上の支払サイト')
    more_than_payment_method = fields.Selection(PAYMENT_METHOD,
        string='万円以上の支払手段', default='transfer')
    less_than_amount = fields.Float(string='万円以下金額')
    less_than_deadline = fields.Char(
        string='万円以下の締日')
    less_than_payment_site = fields.Char(
        string='万円以下の支払サイト')
    less_than_payment_method = fields.Selection(PAYMENT_METHOD,
        string='万円以下の支払手段', default='transfer')
    collecting_money = fields.Selection([
        ('yes', '有'),
        ('no', '無'),
    ], string='集金', default='no')
    fee_burden = fields.Selection([
        ('other_side', '先方'),
        ('our_side', '当方'),
    ], string='手数料負担', default='our_side')
    bill_site = fields.Char(string='手形サイト')
    partner_id = fields.Many2one('res.partner', '連絡先')
