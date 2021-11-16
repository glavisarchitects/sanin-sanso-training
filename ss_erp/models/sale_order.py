# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_organization_id = fields.Many2one('ss_erp.organization', string="販売組織", copy=False)
    x_responsible_dept_id = fields.Many2one('ss_erp.responsible.department', string="管轄部門", copy=False)
    x_no_approval_required_flag = fields.Boolean('承認不要フラグ?')
    approval_status = fields.Selection(
        string='承認済み区分',
        selection=[('out_of_process', '未承認'),
                   ('in_process', '承認中'),
                   ('approved','承認済み')],
        required=False, default='out_of_process')

    def action_confirm(self):
        if not self.x_no_approval_required_flag and self.approval_status != 'approved':
            raise UserError(_("Please complete approval flow before change to order"))
        return super(SaleOrder, self).action_confirm()

    def action_quotation_sent(self):
        if self.filtered(lambda so: not so.x_no_approval_required_flag and so.approval_status != 'approved'):
            raise UserError(_('Only approved orders can be marked as sent directly.'))
        super(SaleOrder, self).action_quotation_sent()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # TODO: Need re check
    x_pricelist = fields.Many2one('product.pricelist', string="価格リスト", index=True)
    x_expected_delivery_date = fields.Date("納期予定日")
    x_remarks = fields.Char("備考")