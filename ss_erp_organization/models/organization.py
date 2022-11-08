# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Organization(models.Model):
    _name = 'ss_erp.organization'
    _description = '組織'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='組織名称')
    company_id = fields.Many2one(
        'res.company', string='会社', required=True,
        default=lambda self: self.env.company)
    sequence = fields.Integer("シーケンス")
    active = fields.Boolean(
        default=True,
        help="If the active field is set to False, it will allow you to hide the payment terms without removing it.")
    expire_start_date = fields.Date(string="有効開始日", copy=False)
    expire_end_date = fields.Date(string="有効終了日", copy=False,
                                  default=lambda self: fields.Date.today().replace(month=12, day=31, year=2099))
    parent_path = fields.Char(index=True)
    organization_code = fields.Char(
        string="組織コード", required=True, copy=False)
    organization_category_id = fields.Many2one(
        "ss_erp.organization.category", string="組織カテゴリ", ondelete="restrict",
        check_company=True, help="組織カテゴリ")
    parent_id = fields.Many2one(
        "ss_erp.organization", string="親組織", )
    parent_organization_code = fields.Char(
        string="親組織コード", compute="_compute_parent_organization_code", compute_sudo=True)
    organization_country_id = fields.Many2one(
        "res.country", string="組織住所/国", default=lambda self: self.env.ref('base.jp', raise_if_not_found=False))
    organization_zip = fields.Char(string="組織住所/郵便番号")
    organization_state_id = fields.Many2one(
        "res.country.state", string="組織住所/都道府県")
    organization_city = fields.Char("組織住所/市区町村")
    organization_street = fields.Char("組織住所/町名番地")
    organization_street2 = fields.Char(
        "組織住所/町名番地2")
    organization_phone = fields.Char("組織代表Tel")
    organization_fax = fields.Char("組織代表Fax")
    complete_name = fields.Char(
        '組織名称', compute='_compute_complete_name',
        store=True)

    organization_address = fields.Char(string='住所', compute='_compute_organization_address',store=True)

    @api.depends('organization_state_id', 'organization_city','organization_street','organization_street2')
    def _compute_organization_address(self):
        for rec in self:
            full_address = ''
            full_address += rec.organization_state_id.name or ''
            full_address += rec.organization_city or ''
            full_address += rec.organization_street or ''
            full_address += rec.organization_street2 or ''
            rec.organization_address = full_address

    # TuyenTN 2022/07/15
    bank_ids = fields.One2many('res.partner.bank', string='銀行口座', inverse_name='organization_id')
    responsible_person = fields.Many2one('hr.employee', string='責任者')

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

    @api.constrains("expire_start_date", "expire_end_date")
    def _check_dates(self):
        """End date should not be before start date, if not filled

        :raises ValidationError: When constraint is violated
        """
        for record in self:
            if (
                    record.expire_start_date
                    and record.expire_end_date
                    and record.expire_start_date > record.expire_end_date
            ):
                raise ValidationError(
                    _("有効開始日は、終了日より先の日付は選択できません")
                )

    @api.constrains("expire_start_date", "expire_end_date", "organization_code")
    def _check_organization_duration(self):
        for record in self:
            if record and record.organization_code:
                organization_ids = self.env['ss_erp.organization'].search(
                    [('organization_code', '=', record.organization_code)])
                for org in organization_ids:
                    if record != org:
                        if record.expire_start_date and org.expire_start_date and org.expire_end_date:
                            if org.expire_start_date <= record.expire_start_date <= org.expire_end_date:
                                raise ValidationError(_("組織コードは有効期間内でユニークでなければなりません。"))
                        if record.expire_end_date and org.expire_start_date and org.expire_end_date:
                            if org.expire_start_date <= record.expire_end_date <= org.expire_end_date:
                                raise ValidationError(_("組織コードは有効期間内でユニークでなければなりません。"))

    @api.constrains('parent_id')
    def _check_organization_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('再帰的な組織を作成することはできません。'))
        return True

    def action_unarchive(self):
        organization_ids = self.env['ss_erp.organization'].search([('organization_code', '=', self.organization_code)])
        for org in organization_ids:
            if self != org:
                if (org.expire_start_date <= self.expire_start_date <= org.expire_end_date) or (
                        org.expire_start_date <= self.expire_end_date <= org.expire_end_date):
                    raise ValidationError(_("組織コードは有効期間内でユニークでなければなりません。"))
        return super(Organization, self).action_unarchive()

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
