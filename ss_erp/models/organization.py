# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Organization(models.Model):
    _name = 'ss_erp.organization'
    _description = 'Organization'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='組織名称')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company)
    sequence = fields.Integer("Sequence")
    active = fields.Boolean(
        default=True, help="If the active field is set to False, it will allow you to hide the payment terms without removing it.")
    date_start = fields.Date(string="Valid start date", copy=False)
    date_end = fields.Date(string="Expiration date", copy=False,
                           default=lambda self: fields.Date.today().replace(month=12, day=31, year=2099))
    # child_ids = fields.One2many('ss_erp.organization', 'parent_id',
    #                             string="Contains Organizations")
    parent_path = fields.Char(index=True)
    organization_code = fields.Char(
        string="Organization Code", required=True, copy=False)
    organization_category_id = fields.Many2one(
        "ss_erp.organization.category", string="Organization category", ondelete="restrict",
        check_company=True, help="Category of this organization")
    parent_id = fields.Many2one(
        "ss_erp.organization", string="Parent organization", )
    parent_organization_code = fields.Char(
        string="Parent organization code", compute="_compute_parent_organization_code", compute_sudo=True)
    organization_country_id = fields.Many2one(
        "res.country", string="Organization address / country", default=lambda self: self.env.ref('base.jp', raise_if_not_found=False))
    organization_zip = fields.Char(string="Organization address / zip code")
    organization_state_id = fields.Many2one(
        "res.country.state", string="Organization address / prefecture")
    organization_city = fields.Char("Organization Address / City")
    organization_street = fields.Char("Organization address / town name")
    organization_street2 = fields.Char(
        "Organization address / town name address 2")
    organization_phone = fields.Char("Organization phone number")
    organization_fax = fields.Char("Organization Representative Fax")
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        store=True)

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for organization in self:
            if organization.parent_id:
                organization.complete_name = '%s / %s' % (
                    organization.parent_id.complete_name, organization.name)
            else:
                organization.complete_name = organization.name

    @api.depends('parent_id', 'parent_id.organization_code')
    def _compute_parent_organization_code(self):
        for record in self:
            record.parent_organization_code = record.parent_id.organization_code if record.parent_id else ''

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        """End date should not be before start date, if not filled

        :raises ValidationError: When constraint is violated
        """
        for record in self:
            if (
                record.date_start
                and record.date_end
                and record.date_start > record.date_end
            ):
                raise ValidationError(
                    _("The starting date cannot be after the ending date.")
                )

    @api.constrains('parent_id')
    def _check_organization_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('再帰的な組織を作成することはできません。'))
        return True

    def action_unarchive(self):
        organization_count = self.env['ss_erp.organization'].search_count(
            [('organization_code', '=', self.organization_code)])
        if organization_count > 0:
            raise ValidationError(_("組織コードはユニークでなければなりません。"))
        return super(Organization, self).action_unarchive()

    @api.constrains('organization_code')
    def _check_organization_code(self):
        for record in self:
            organization_count = self.search_count(
                [('organization_code', '=', record.organization_code)])
            if organization_count > 1:
                raise ValidationError(_("組織コードはユニークでなければなりません。"))

    @api.model
    def _get_default_address_format(self):
        return "%(city)s %(street)s %(street2)s"

    def _display_address(self, without_company=False):

        address_format = self._get_default_address_format()
        args = {
            'street': self.organization_street or '',
            'street2': self.organization_street2 or '',
            'city': self.organization_city or '',
            'zip': self.organization_zip or '',
            'state_code': self.organization_state_id and self.organization_state_id.code or '',
            'state_name': self.organization_state_id and self.organization_state_id.name or '',
            'country_code': self.organization_country_id and self.organization_country_id.code or '',
            'country_name': self.organization_country_id and self.organization_country_id.name or '',
        }

        address_format = '' + address_format
        return address_format % args
