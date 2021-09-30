# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_warning_qty_product_purchase = fields.Boolean("PO Quantity Warning", implied_group='x_purchase_order.group_warning_qty_product_purchase')
    group_warning_amount_product_purchase = fields.Boolean("PO Amount Warning", implied_group='x_purchase_order.group_warning_amount_product_purchase')
    group_warning_unit_product_purchase = fields.Boolean("PO Unit Warning", implied_group='x_purchase_order.group_warning_unit_product_purchase')
