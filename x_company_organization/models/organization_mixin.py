from odoo import models, fields, _, api
from odoo.exceptions import ValidationError, AccessError
from odoo.osv.expression import AND


class OrganizationMixin(models.AbstractModel):
    _name = "x.x_company_organization.org_mixin"
    _description = "Organization Mixin"

    x_organization_id = fields.Many2one(
        comodel_name="x.x_company_organization.res_org", string="Organization", copy=False,
        default=lambda self: self.env.user.x_organization_id and self.env.user.x_organization_id.id,
        help="Organization which create this record."
    )

    def write(self, vals):
        return super(OrganizationMixin, self).write(vals)

    def read(self, fields=None, load='_classic_read'):
        return super(OrganizationMixin, self).read(fields=fields, load=load)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if not self.user_has_groups("x_security_groups.group_branch_manager"):
            args = AND([["|",
                         ("x_organization_id", "=", False),
                         ("x_organization_id", "child_of", self.env.user.x_organization_id.id)],
                         args]
            )
        return super(OrganizationMixin, self).search(args, offset=offset, limit=limit, order=order, count=count)

    def browse(self, ids=None):
        return super(OrganizationMixin, self).browse(ids=ids)

    def unlink(self):
        if not self.user_has_groups("x_security_groups.group_head_quarter"):
            current_user_org_id = self.env.user.x_organization_id and self.env.user.x_organization_id.id
            for r in self:
                if str(current_user_org_id) not in r.x_organization_id.parent_path:
                    raise AccessError(_("You can not delete a record which is not"
                                        " directly belongs to your organization!"))
        return super(OrganizationMixin, self).unlink()
