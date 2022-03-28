# -*- coding: utf-8 -*-

from . import models
from . import wizards
from . import controllers
from odoo import api, SUPERUSER_ID

EDIT_CREATE_PARTNER_ACCESS_RIGHTS = [
    "crm.access_res_partner",
    "hr_recruitment.access_res_partner_hr_user",
    "mrp.access_product_group_res_partner_mrp_manager",
    "purchase.access_res_partner_purchase_manager",
    "sale.access_res_partner_sale_manager",
    "sale.access_product_group_res_partner_sale_manager",
    "stock.access_product_group_res_partner_stock_manager",
    "base.access_res_partner_group_partner_manager",
]

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for access_right_name in EDIT_CREATE_PARTNER_ACCESS_RIGHTS:
        group_access_right = env.ref(access_right_name, raise_if_not_found=False)
        if group_access_right:
            group_access_right.write({
                "perm_write": False,
                "perm_create": False,
            })

def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for access_right_name in EDIT_CREATE_PARTNER_ACCESS_RIGHTS:
        group_access_right = env.ref(access_right_name, raise_if_not_found=False)
        if group_access_right:
            group_access_right.write({
                "perm_write": True,
                "perm_create": True
            })
