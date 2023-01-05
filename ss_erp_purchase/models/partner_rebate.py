# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
from datetime import datetime
import pytz


class PartnerRebate(models.Model):
    _name = 'ss_erp.partner.rebate'
    _description = 'リベート条件'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'partner_id'

    def _get_default_date_start(self):
        dt = datetime.strptime(str(fields.Datetime.now().replace(hour=0, minute=0, second=0)), '%Y-%m-%d %H:%M:%S')
        user = self.env.user
        if user and user.tz:
            user_tz = user.tz
            if user_tz in pytz.all_timezones:
                old_tz = pytz.timezone('UTC')
                new_tz = pytz.timezone(user_tz)
                dt = new_tz.localize(dt).astimezone(old_tz)
            else:
                _logger.info(_("Unknown timezone {}".format(user_tz)))
        return datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')

    def _get_default_date_end(self):
        dt = datetime.strptime(str(fields.Datetime.now().replace(hour=23, minute=59, second=59)), '%Y-%m-%d %H:%M:%S')
        user = self.env.user
        if user and user.tz:
            user_tz = user.tz
            if user_tz in pytz.all_timezones:
                old_tz = pytz.timezone('UTC')
                new_tz = pytz.timezone(user_tz)
                dt = new_tz.localize(dt).astimezone(old_tz)
            else:
                _logger.info(_("Unknown timezone {}".format(user_tz)))
        return datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')

    def _get_default_x_organization_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id.organization_first
        else:
            return False

    def _get_default_x_responsible_dept_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id and employee_id.department_jurisdiction_first:
            return employee_id.department_jurisdiction_first
        else:
            return False

    name = fields.Char(string='名称', default='新規', readonly=1)
    sequence = fields.Integer(string='シーケンス', default=10)
    company_id = fields.Many2one(
        "res.company", string="会社情報",
        default=lambda self: self.env.company.id, index=True
    )
    organization_id = fields.Many2one(
        comodel_name="ss_erp.organization", string="担当組織",
        copy=False, index=True, default=lambda self: self._get_default_x_organization_id()
    )
    responsible_id = fields.Many2one(
        'ss_erp.responsible.department', "管轄部門", index=True,
        default=lambda self: self._get_default_x_responsible_dept_id())
    partner_id = fields.Many2one(
        'res.partner', string='仕入先',
        change_default=True, tracking=True, index=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )
    partner_ref = fields.Char(
        related='partner_id.ref',
        string="仕入先コード")

    active = fields.Boolean(
        string="Enable", default=True,
        help="Set active to false to hide the rebate contract without removing it.")
    date_start = fields.Datetime(
        string="契約開始日",
        default=_get_default_date_start)

    date_end = fields.Datetime(
        string="契約終了日",
        default=_get_default_date_end)
    rebate_price = fields.Float("報奨金", )
    rebate_standard = fields.Text("報奨金の基準")
    memo = fields.Text("備考")
    rebate_goal = fields.Char("目標")
    rebate_products = fields.Text("対象品")
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id)
    attachment_number = fields.Integer(
        '添付数', compute='_compute_attachment_number')

    register_id = fields.Many2one('res.users', "登録者", )
    user_id = fields.Many2one(
        comodel_name='res.users', default=lambda self: self.env.uid)

    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([
            ('res_model', '=', 'ss_erp.partner.rebate'),
            ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict(
            (data['res_id'], data['res_id_count']) for data in attachment_data)
        for record in self:
            record.attachment_number = attachment.get(record.id, 0)

    # @api.constrains("register_id", "organization_id")
    # def _check_register_id(self):
    #     for record in self:
    #         if record.organization_id not in record.register_id.organization_ids:
    #             raise ValidationError(_("登録者の所属組織と担当組織が異なるため保存できません。"))

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        """End date should not be before start date, if not filled

        :raises ValidationError: When constraint is violated
        """
        for record in self:
            if record.date_start and record.date_end:
                if record.date_start > record.date_end:
                    raise ValidationError(_("契約開始日は、契約終了日より先の日付は選択できません。"))
                elif record.date_start == record.date_end:
                    raise ValidationError(_("契約開始日と契約終了日が同じ日時になっています。"))

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id(
            'base.action_attachment')
        res['domain'] = [('res_model', '=', 'ss_erp.partner.rebate'),
                         ('res_id', 'in', self.ids)]
        res['context'] = {
            'default_res_model': 'ss_erp.partner.rebate', 'default_res_id': self.id}
        return res

    def action_add_attachment(self):
        action = {
            'name': _("添付ファイル"),
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'target': 'new',
            'context': {
                'default_rebate_id': self.id,
            },
            'res_model': 'partner.rebate.attachment.wizard'
        }
        return action
