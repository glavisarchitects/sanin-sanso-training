from odoo import models, _
from odoo.exceptions import ValidationError


class PortalMixin(models.AbstractModel):
    _inherit = "portal.mixin"

    def _get_share_url(self, redirect=False, signup_partner=False, pid=None, share_token=True):
        if self._context.get("active_model", "") == "sale.order":
            order = self.env[self._context.get("active_model", "")].browse(
                self._context.get("active_id", 0)).sudo()
            if order and order.approval_state != "approved":
                raise ValidationError(_("You shouldn't share a quotation which is not yet approved!"))
        return super(PortalMixin, self)._get_share_url(redirect, signup_partner, pid, share_token)
