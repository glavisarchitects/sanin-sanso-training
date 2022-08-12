# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import base64


class PartnerRebateAttachmentWizard(models.TransientModel):
    _name = 'partner.rebate.attachment.wizard'
    _description = 'Attachment file'


    file = fields.Binary(string='File', required=True, )
    filename = fields.Char()
    rebate_id = fields.Many2one('ss_erp.partner.rebate', 'Rebate condition')

    def action_confirm(self):
        self.env['ir.attachment'].create({
            'name': self.filename,
            'res_id': self.rebate_id.id,
            'datas': self.file,
            'res_model': 'ss_erp.partner.rebate',
        })
        return True
