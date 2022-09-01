from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    partner_form_id = fields.Many2one('ss_erp.res.partner.form', 'Account Holder', ondelete='cascade')

    @api.model
    def create(self, vals):
        if vals.get('partner_id'):
            partner_form_id = self.env['ss_erp.res.partner.form'].search([('res_partner_id', '=', vals.get('partner_id'))])
            if partner_form_id:
                vals['partner_form_id'] = partner_form_id.id
        return super(ResPartnerBank, self).create(vals)


