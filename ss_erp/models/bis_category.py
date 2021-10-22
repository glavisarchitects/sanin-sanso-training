from odoo import fields, models


class TransactionClassification(models.Model):
    _name = "ss_erp.bis.category"
    _description = "TransactionClassification"

    name = fields.Char(
        string="取引区分", index=True, required=True
    )
    department = fields.Char(
        string="部門", index=True
    )
