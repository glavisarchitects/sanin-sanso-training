# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID, _


class SettingRequest(models.Model):
    """
    model setting partner request
    """
    _name = "x.res.setting.request"
    _description = 'Setting Request'

    name = fields.Char()
    step_approval = fields.Selection([('step1', '1次承認待ち'), ('step2', '2次承認待ち'), ('step3', '3次承認待ち')], string="承認ステップ設定")
    branch_approver_id = fields.Many2one("hr.employee", string="1次承認者")
    sale_hq_approver_ids = fields.Many2many("hr.employee", "sale_hq_approver_employee_rel", string="2次承認者")
    account_hq_approver_ids = fields.Many2many("hr.employee", "account_hq_approver_employee_rel", string="最終承認者")

    def show_list_aprover(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Request Approval"),
            "target": "new",
            "res_model": "hr.employee",
            "view_mode": "tree",
            # "context": {
            #     "default_x_partner_request_id": self.id,
            # }
        }
