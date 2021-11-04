# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_organization_id = fields.Many2one('ss_erp.organization', string="販売支店", copy=False)
    x_responsible_dept_id = fields.Many2one('ss_erp.responsible.department', string="管轄部門", copy=False)

    # TODO: Need re confirm  x_import_id
    x_import_id = fields.Char("Import ID")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # TODO: Need re check
    x_pricelist = fields.Many2one('product.pricelist', string="価格リスト", index=True)
    x_expected_delivery_date = fields.Date("納期予定日")