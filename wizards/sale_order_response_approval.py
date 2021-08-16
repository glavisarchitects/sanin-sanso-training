from odoo import models, fields, _
from odoo.exceptions import ValidationError


class SaleOrderResponseApproval(models.TransientModel):
    _name = "sale.order.response.approval"
    _description = "Response for Sale quotation request of approval"

    sale_order_id = fields.Many2one("sale.order", string="Sale Order", readonly=True, copy=False)
    response = fields.Selection(
        [("approved", "Approve"), ("rejected", "Reject"), ("remanded", "Remand")],
        string="Response", required=True, default="approved",
        help="Response for this quotation:\n"
             "- Approve: Approving this quotation, salesperson now can sent this quotation to customer.\n"
             "- Remand: To work this quotation again, improving it.\n"
             "- Reject: This quotation is un-improvable, need to re-do it."
    )
    note = fields.Char(string="Compliment", help="Compliment for this action!")

    def accept(self):
        if self.env.user.id != self.sale_order_id.crm_team_leader_user_id.id:
            raise ValidationError(_("You are not permitted to approve this quotation!"))
        self.ensure_one()
        self.sale_order_id.with_context(request_approval_response=True).write(
            {"approval_state": self.response}
        )
        self.sale_order_id.sudo().response_to_request_approval(self.note)
