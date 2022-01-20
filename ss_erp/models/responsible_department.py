# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResponsibleDepartment(models.Model):
    _name = 'ss_erp.responsible.department'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Responsible Department'

    name = fields.Char(string='Name')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)
    sequence = fields.Integer("Sequence")
    active = fields.Boolean(
        default=True, )
    start_date = fields.Date(string="Valid start date", copy=False)
    end_date = fields.Date(string="Expiration date", copy=False,
                           default=lambda self: fields.Date.today().replace(month=12, day=31, year=2099))
    code = fields.Char(string="Code", copy=False)

    @api.constrains("code", "name", "company_id")
    def _check_code(self):
        for record in self:
            responsible_department_ids = record.env['ss_erp.responsible.department'].search(
                [('code', '=', record.code), ('name', '=', record.name), ('company_id', '=', record.company_id.id)])
            for department in responsible_department_ids:
                if record != department:
                    if (department.start_date <= record.start_date <= department.end_date) or (
                                department.start_date <= record.end_date <= department.end_date):
                        raise ValidationError(_("管轄部門は有効期間内でユニークでなければなりません。"))

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
