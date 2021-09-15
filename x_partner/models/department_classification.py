from odoo import fields, models, _
from odoo.exceptions import ValidationError


class TransactionClassification(models.Model):
    _name = "x.transaction.classification"
    _description = "Transaction Classification"

    name = fields.Char("Transaction", translate=True, required=True)
    default = fields.Boolean("Default?")
    description = fields.Text("Note fields")

    def unlink(self):
        if self.env.ref("x_partner.transaction_classification_gas_equipment") in self or\
            self.env.ref("x_partner.transaction_classification_construction") in self:
            raise ValidationError(_("Base transaction classify can not be deleted!"))
        return super(TransactionClassification, self).unlink()

class DepartmentClassification(models.Model):
    _name = "x.department.classification"
    _description = "Department Classification"

    name = fields.Char("Transaction", translate=True, required=True)
    default = fields.Boolean("Default?")
    description = fields.Text("Note fields")
    transaction_classify_id = fields.Many2one(
        comodel_name="x.transaction.classification", string="Transaction Classify",
        ondelete="restrict", required=True, copy=False
    )
