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

    organization_id = fields.Many2one(
        comodel_name='ss_erp.organization',
        string='組織情報',
        required=False)
    partner_id = fields.Many2one('res.partner', 'Contact address')
    total_amount = fields.Float(string='取引条件金額')
    range = fields.Selection([('up', '以上'), ('down', '未満')], string='単位')
    payment_term = fields.Char(string='支払サイト')
    receipt_type_branch = fields.Selection(
        [('bank', '振込'),
         ('transfer', '振替'),
         ('bills', '手形'),
         ('cash', '現金'),
         ('paycheck', '小切手'),
         ('branch_receipt', '他店入金'),
         ('offset', '相殺')],
        string='入金手段'
    )
    collecting_money = fields.Selection(
        [('yes', '有'), ('no', '無')], string='集金', default='no'
    )

    fee_burden = fields.Selection(
        string='手数料負担',
        selection=[('other_side', '先方負担'),
                   ('our_side', '当社負担'), ],
        default='our_side',
        required=False, )
