from odoo import models, _
from odoo.exceptions import ValidationError


class SalePaymentLink(models.TransientModel):
    _inherit = "payment.link.wizard"

    def _generate_link(self):
        for r in self:
            if r.res_model == "sale.order":
                sale_order = self.env[r.res_model].browse(r.res_id).sudo()
                if sale_order.approval_state != "approved":
                    raise ValidationError(_("You shouldn't share a quotation which is not yet approved!"))
                super(SalePaymentLink, r)._generate_link()
