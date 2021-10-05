# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PartnerRebate(models.Model):
    _name = 'x.partner.rebate'
    _description = 'Rebate condition'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    def _default_employee(self):
        return self.env.user.employee_id

    name = fields.Char(string='No.', default='New', readonly=1)
    sequence = fields.Integer(string='Sequence', default=10)
    company_id = fields.Many2one(
        "res.company", string="Company", required=True,
        default=lambda self: self.env.company.id
    )
    x_organization_id = fields.Many2one(
        comodel_name="x.x_company_organization.res_org", string="Organization",
        copy=False, default=lambda self: self._default_organization_id(),
        help="Organization which create this record."
    )
    jurisdiction_id = fields.Many2one('crm.team', "Jurisdiction")
    partner_id = fields.Many2one(
        'res.partner', string='Supplier',
        required=True, change_default=True, tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    partner_code = fields.Char(
        related='partner_id.x_partner_code',
        string="Supplier code")
    employee_id = fields.Many2one(
        'hr.employee', string="Employee",
        default=_default_employee, required=True, ondelete='cascade', index=True)
    active = fields.Boolean(
        string="Enable", default=True,
        help="Set active to false to hide the rebate contract without removing it.")
    date_start = fields.Datetime(string="Contract start date", copy=False)
    date_end = fields.Datetime(string="Contract end date", copy=False)
    bonus_money = fields.Float("Bonus money")
    reward_criteria = fields.Text("Reward criteria")
    remark = fields.Text("Remark")
    target = fields.Char("Target")
    product_target = fields.Char("Product target")
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id)
    attachment_number = fields.Integer(
        'Number of Attachments', compute='_compute_attachment_number')

    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([
            ('res_model', '=', 'x.partner.rebate'),
            ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict(
            (data['res_id'], data['res_id_count']) for data in attachment_data)
        for record in self:
            record.attachment_number = attachment.get(record.id, 0)

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

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'x.partner.rebate') or _('New')
        result = super(PartnerRebate, self).create(vals)
        return result

    @api.model
    def _default_organization_id(self):
        return self.env.user.x_organization_id and self.env.user.x_organization_id.id

    @api.model
    def compute_year(self, date_end):
        """PhuongTN: calculate the distance between date_end and current date"""
        days_in_year = 365.2425
        year = int((fields.Datetime.now() - date_end).days / days_in_year)
        return year

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id(
            'base.action_attachment')
        res['domain'] = [('res_model', '=', 'x.partner.rebate'),
                         ('res_id', 'in', self.ids)]
        res['context'] = {
            'default_res_model': 'x.partner.rebate', 'default_res_id': self.id}
        return res

    def action_add_attachment(self):
        action = {
            'name': _("Attachment file"),
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'target': 'new',
            'context': {
                'default_rebate_id': self.id,
            },
            'res_model': 'partner.rebate.attachment.wizard'
        }
        return action
