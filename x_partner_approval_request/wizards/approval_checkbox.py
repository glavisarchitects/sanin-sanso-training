from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class ApprovalCheckbox(models.TransientModel):
    _name = "x.approval.checkbox"
    _description = "Approval Checkbox"

    x_partner_request_id = fields.Many2one("x.res.partner.newrequest")

    def confirm_request(self):
        if self.x_partner_request_id.state == "sale_head_approval":
            self.x_partner_request_id.state = "branch_manager_approval"
