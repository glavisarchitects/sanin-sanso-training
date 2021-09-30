# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import base64


class PurchaseConfirmWizard(models.TransientModel):
    _name = 'purchase.order.confirm.wizard'
    _description = 'Purchase Confirm Wizard'

    msg = fields.Text("Msg")
    po_id = fields.Many2one('purchase.order', 'Purchase order')
    type = fields.Selection([('nothing', ""), ('cancel', "Cancel"), ('confirm', "Confirm")], "Type", default="nothing")

    def action_confirm(self):
        self.po_id.button_confirm()
        return True

    def action_cancel(self):
        self.po_id.button_cancel()
        return True
