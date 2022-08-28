# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResponsibleDepartment(models.Model):
    _name = 'ss_erp.responsible.department'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Responsible Department'
    _order = "code asc, start_date asc"

    name = fields.Char(string='管轄部門名称')
    company_id = fields.Many2one(
        'res.company', string='会社',
        default=lambda self: self.env.company)
    sequence = fields.Integer("シーケンス")
    active = fields.Boolean(
        default=True, )
    start_date = fields.Date(string="有効開始日", copy=False)
    end_date = fields.Date(string="有効終了日", copy=False,
                           default=lambda self: fields.Date.today().replace(month=12, day=31, year=2099))
    code = fields.Char(string="管轄部門コード", copy=False)

    @api.constrains("code", "company_id", "start_date", "end_date")
    def _check_code(self):
        for record in self:
            responsible_department_ids = record.env['ss_erp.responsible.department'].search(
                [('code', '=', record.code), ('company_id', '=', record.company_id.id)])
            for department in responsible_department_ids:
                if record != department:
                    if (department.start_date <= record.start_date <= department.end_date) or (
                                department.start_date <= record.end_date <= department.end_date):
                        raise ValidationError(_("管轄部門は有効期間内でユニークでなければなりません。"))

    def action_unarchive(self):
        responsible_department_ids = self.env['ss_erp.responsible.department'].search(
            [('code', '=', self.code), ('company_id', '=', self.company_id.id)])
        for department in responsible_department_ids:
            if self != department:
                if (department.start_date <= self.start_date <= department.end_date) or (
                        department.start_date <= self.end_date <= department.end_date):
                    raise ValidationError(_("管轄部門は有効期間内でユニークでなければなりません。"))
        return super(ResponsibleDepartment, self).action_unarchive()

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
                    _("有効開始日は、終了日より先の日付は選択できません。")
                )
