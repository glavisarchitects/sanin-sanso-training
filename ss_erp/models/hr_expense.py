# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    x_sub_account_id = fields.Many2one('ss_erp.account.subaccount', string='補助科目')
    x_request_date = fields.Date(string='申請日')
    x_organization_id = fields.Many2one('ss_erp.organization', string='申請組織')
    x_responsible_id = fields.Many2one('ss_erp.responsible.department', string='申請部署')
    # sale_order_id = fields.Many2one('sale.order', string='顧客請求受注伝票')

    @api.onchange('account_id')
    def onchange_sub_account_id(self):
        if self.account_id:
            self.x_sub_account_id = self.env['account.account'].search(
                [('x_sub_account_ids', 'in', self.account_id.id)]).id
