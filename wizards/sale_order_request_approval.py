from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class SaleOrderRequestApproval(models.TransientModel):
    _name = "sale.order.request.approval"
    _description = "Request Approval for Sale Quotation"

    sale_order_id = fields.Many2one("sale.order", string="Sale Order")
    crm_team_id = fields.Many2one("crm.team", string="Branch", required=True)
    request_deadline = fields.Datetime(string="Deadline", required=True)
    note = fields.Char(string="Note")

    @api.constrains("request_deadline")
    def _check_request_deadline(self):
        for r in self:
            if r.request_deadline < fields.Datetime.now():
                raise ValidationError(_("You can not set a deadline which is in the past!"))

    def request(self):
        if not self.user_has_groups("sales_team.group_sale_salesman"):
            raise ValidationError(_("You are not permitted to request approval for sale quotation!"))
        self.ensure_one()
        self.sale_order_id.sudo().write({
            "approval_date_ends": self.request_deadline,
        })
        self.sale_order_id.request_approval(self.note)
