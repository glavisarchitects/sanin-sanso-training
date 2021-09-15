from odoo import fields, models, _, api
from odoo.exceptions import ValidationError


class TransactionClassification(models.Model):
    _name = "x.transaction.classification"
    _description = "Transaction Classification"

    name = fields.Char("Transaction", translate=True)
    default = fields.Boolean("Default?")
    description = fields.Char("Note fields")

    def unlink(self):
        if self.env.ref("x_partner.transaction_classification_gas_equipment") in self:
            raise ValidationError(_("Base transaction classify can not be deleted!"))
        return super(TransactionClassification, self).unlink()
