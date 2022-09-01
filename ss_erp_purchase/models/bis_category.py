from odoo import fields, models


class TransactionClassification(models.Model):
    _name = "ss_erp.bis.category"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "TransactionClassification"

    name = fields.Char(
        string="取引区分", index=True, required=True
    )
    department = fields.Char(
        string="部門", index=True
    )
    active = fields.Boolean(
        'Active', default=True,)