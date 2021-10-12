# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResponsibleDepartment(models.Model):
    _name = 'ss.erp.responsible.department'

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
    code = fields.Char(string="Code", copy=False)

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
