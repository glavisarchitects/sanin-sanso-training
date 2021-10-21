# -*- coding: utf-8 -*-

from . import models
from odoo import api, SUPERUSER_ID


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    report_purchase_quotation = env.ref('purchase.report_purchase_quotation')
    if report_purchase_quotation and report_purchase_quotation.binding_model_id:
        report_purchase_quotation.unlink_action()
    report_purchase_order = env.ref('purchase.action_report_purchase_order')
    if report_purchase_order and report_purchase_order.binding_model_id:
        report_purchase_order.unlink_action()

def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    report_purchase_quotation = env.ref('purchase.report_purchase_quotation')
    if report_purchase_quotation and report_purchase_quotation.binding_model_id:
        report_purchase_quotation.create_action()
    report_purchase_order = env.ref('purchase.action_report_purchase_order')
    if report_purchase_order and report_purchase_order.binding_model_id:
        report_purchase_order.create_action()
