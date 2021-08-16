from datetime import timedelta
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = ["sale.order"]

    crm_team_id = fields.Many2one(
        "crm.team", string="Branch", default=lambda self: self.env.user.sale_team_id.id,
        readonly=True, help="The branch which create this sale quotation.")
    crm_team_leader_user_id = fields.Many2one(
        "res.users", string="Approve By", related="crm_team_id.user_id",
        help="Authorize person whom can approve/ remand/ reject this quotation.")
    approval_state = fields.Selection(
        [("draft", "Draft"), ("requested", "Requested"), ("approved", "Approved"),
         ("rejected", "Rejected"), ("remanded", "Remanded")],
        string="Approval State", required=True, default="draft", tracking=True, copy=False,
        readonly=True, help="Approval state for this quotation."
    )
    approval_date_ends = fields.Datetime(
        string="Approval Date Ends", readonly=True,
        help="Approval deadline, this quotation should be reviewed before this day"
    )
    delivery_info = fields.Many2one("res.users", string="Delivery Info")

    def write(self, vals):
        if self.filtered(lambda so: so.approval_state in ["requested", "rejected"]):
            if not self._context.get("request_approval_response", False):
                raise ValidationError(_("Requested or rejected quotation can not be edited!"))
        return super(SaleOrder, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(SaleOrder, self).create(vals_list)
        for r in res:
            if r.crm_team_leader_user_id:
                r.message_subscribe(partner_ids=r.crm_team_leader_user_id.ids)
        return res

    def action_quotation_sent(self):
        if self.filtered(lambda so: so.approval_state != "approved"):
            raise ValidationError(_("Quotations must be approved before sending to customers."))
        return super(SaleOrder, self).action_quotation_sent()

    def action_quotation_send(self):
        self.ensure_one()
        if self.approval_state != "approved":
            raise ValidationError(_("Quotation must be approved before sending to customer."))
        return super(SaleOrder, self).action_quotation_send()

    def action_confirm(self):
        if self.filtered(lambda so: so.approval_state != "approved"):
            raise ValidationError(_("Quotations must be approved before confirming."))
        return super(SaleOrder, self).action_confirm()

    def action_request_approval(self):
        self.ensure_one()
        if not self.crm_team_leader_user_id:
            self.approval_state = "approved"
            return
        if self.approval_state not in ["draft", "remanded"]:
            raise ValidationError(_("Only draft or remanded quotation can be requested for approval!"))
        if self.approval_date_ends:
            request_deadline = self.approval_date_ends
        else:
            request_deadline = (self.date_order + timedelta(days=7))
        return {
            "type": "ir.actions.act_window",
            "name": _("Request Approval"),
            "target": "new",
            "res_model": "sale.order.request.approval",
            "view_mode": "form",
            "context": {
                "default_sale_order_id": self.id,
                "default_request_deadline": request_deadline,
                "default_crm_team_id": self.crm_team_id.id,
            },
        }

    def request_approval(self, note):
        self.ensure_one()
        msg_data_to_create = self._prepare_request_approval()
        if note:
            msg_data_to_create["body"] += "\n%s" % note
        self.with_context(request_approval_response=True).write({
                "approval_state": "requested",
            })
        self.message_post(**msg_data_to_create)
        self.create_approval_mail_activity(note)

    def _prepare_request_approval(self):
        self.ensure_one()
        body = """
<a href="/web#model=res.partner&amp;id=%s class="o_mail_redirect" target="_blank">
  @%s
</a> Please review this quotation before %s.""" % (
            self.crm_team_leader_user_id.partner_id.id,
            self.crm_team_leader_user_id.partner_id.name,
            self.approval_date_ends.strftime("%Y-%m-%d %H:%M:%S"),
        )
        return {
            "author_id": self.env.user.partner_id.id,
            "message_type": "comment",
            "subtype_xmlid": "mail.mt_note",
            "partner_ids": [self.crm_team_leader_user_id.partner_id.id],
            "body": body,
        }

    def action_cancel_request_approval(self):
        self.ensure_one()
        self.with_context(request_approval_response=True).write({
                "approval_state": "draft",
            })

    def action_response_to_request_approval(self):
        self.ensure_one()
        if self.approval_state != "requested":
            raise ValidationError(_("Only requested quotation can be response!"))
        return {
            "type": "ir.actions.act_window",
            "name": _("Approval"),
            "target": "new",
            "res_model": "sale.order.response.approval",
            "view_mode": "form",
            "context": {
                "default_sale_order_id": self.id,
            },
        }

    def response_to_request_approval(self, note):
        self.ensure_one()
        msg_data_to_create = self._prepare_response_for_request_approval()
        if note:
            msg_data_to_create["body"] += "The compliment is:\n`%s`" % note
        self.message_post(**msg_data_to_create)
        self.create_approval_mail_activity(note)

    def _prepare_response_for_request_approval(self):
        self.ensure_one()
        body = """
<a href="/web#model=res.partner&amp;id=%s class="o_mail_redirect" target="_blank">
  @%s
</a> Your sale quotation is %s.""" % (
            self.user_id.partner_id.id,
            self.user_id.partner_id.name,
            self.approval_state,
        )
        return {
            "author_id": self.env.user.partner_id.id,
            "message_type": "comment",
            "subtype_xmlid": "mail.mt_note",
            "body": body,
            "partner_ids": [self.user_id.partner_id.id],
        }

    def create_approval_mail_activity(self, note):
        self.ensure_one()
        self.env["mail.activity"].create(self._prepare_create_approval_activity(note))

    def _prepare_create_approval_activity(self, note):
        self.ensure_one()
        res = {
            "res_model_id": self.env["ir.model"].search([("model", "=", "sale.order")], limit=1).id,
            "res_id": self.id,
            "note": note,
        }
        if self.approval_state == "requested":
            res.update({
                "user_id": self.crm_team_leader_user_id.id,
                "summary": "A request approval quotation is needed your compliment",
                "date_deadline": self.approval_date_ends,
                })
        elif self.approval_state in ["approved", "rejected", "remanded"]:
            res.update({
                "user_id": self.user_id.id,
                "summary": "Your requested approval quotation is %s" % self.approval_state,
                "date_deadline": fields.Date.today()
                })
        return res