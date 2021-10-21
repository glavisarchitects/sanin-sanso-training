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

    name = fields.Char(string='Name')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        readonly=True, default=lambda self: self.env.company)
    sequence = fields.Integer("Sequence")
    active = fields.Boolean(
        default=True, help="If the active field is set to False, it will allow you to hide the payment terms without removing it.")
    start_date = fields.Date(string="Valid start date", copy=False)
    end_date = fields.Date(string="Expiration date", copy=False,
                           default=lambda self: fields.Date.today().replace(month=12, day=31, year=2099))
    child_ids = fields.One2many('ss_erp.organization', 'parent_id',
                                string="Contains Organizations")
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

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        """End date should not be before start date, if not filled

        :raises ValidationError: When constraint is violated
        """
        for record in self:
            if (
                record.start_date
                and record.end_date
                and record.start_date > record.end_date
            ):
                raise ValidationError(
                    _("The starting date cannot be after the ending date.")
                )

    @api.constrains('child_ids')
    def _check_recursion(self):
        if not self._check_m2m_recursion('child_ids'):
            raise ValidationError(_('Recursion found in child server actions'))
