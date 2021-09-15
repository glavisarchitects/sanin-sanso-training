from odoo import models, fields, api
from odoo.exceptions import AccessDenied
from odoo.osv.expression import AND

"""
@note: NOT EVER using this mixin within user (`res.users`) or partner (`res.partner`)
       Recursive reading or browsing security would be a pain to debug and fix.
"""
class OrganizationMixin(models.AbstractModel):
    _name = "x.x_company_organization.org_mixin"
    _description = "Organization Mixin"

    x_organization_id = fields.Many2one(
        comodel_name="x.x_company_organization.res_org", string="Organization",
        copy=False, default=lambda self: self._default_organization_id(),
        help="Organization which create this record."
    )

    @api.model_create_multi
    def create(self, vals_list):
        # default_org_id = self._default_organization_id()
        # organization_ids = set(
        #     [vals.get("x_organization_id", default_org_id) for vals in vals_list]
        # )
        # if len(organization_ids) > 1:
        #     # Case when 1 user trying to create records for multiple organizations
        #     raise AccessDenied
        return super(OrganizationMixin, self).create(vals_list)

    def write(self, vals):
        # if not self.user_has_groups("x_security_groups.group_head_quarter"):
        #     current_user_org_id = self._default_organization_id()
        #     for r in self:
        #         if r.x_organization_id and str(current_user_org_id) not in r.x_organization_id.parent_path:
        #             raise AccessDenied
        return super(OrganizationMixin, self).write(vals)

    def read(self, fields=None, load='_classic_read'):
        # if not self.user_has_groups("x_security_groups.group_branch_manager"):
        #     current_user_org_id = self._default_organization_id()
        #     self = self.filtered(lambda record: not record.x_organization_id or\
        #                          str(current_user_org_id) in record.x_organization_id.parent_path)
        return super(OrganizationMixin, self).read(fields=fields, load=load)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if not self.user_has_groups("x_security_groups.group_branch_manager"):
            args = AND([self._multi_organization_domain(),args])
        return super(OrganizationMixin, self).search(args, offset=offset, limit=limit, order=order, count=count)

    def browse(self, ids=None):
        res = super(OrganizationMixin, self).browse(ids=ids)
        # if res and not self.user_has_groups("x_security_groups.group_branch_manager"):
        #     current_user_org_id = self._default_organization_id()
        #     return res.filtered(lambda record: not record.x_organization_id or\
        #                         str(current_user_org_id) in record.x_organization_id.parent_path)
        return res

    def unlink(self):
        # if not self.user_has_groups("x_security_groups.group_head_quarter"):
        #     current_user_org_id = self._default_organization_id()
        #     for r in self:
        #         if r.x_organization_id and str(current_user_org_id) not in r.x_organization_id.parent_path:
        #             raise AccessDenied
        return super(OrganizationMixin, self).unlink()

    @api.model
    def _multi_organization_domain(self):
        """
        @note: This function returns a domain for multiple organization records filter
        User which belongs to group branch employee only access to records which is
        not having branch, or created by its children branch.

        @return: <list> Odoo domain
        """
        return ["|",
                ("x_organization_id", "=", False),
                ("x_organization_id", "child_of", self.env.user.x_organization_id.id)]

    @api.model
    def _default_organization_id(self):
        """
        @note: This function returns current user organization (if has)

        @return: <int> x_organization_id of current user
        """
        return self.env.user.x_organization_id and self.env.user.x_organization_id.id
