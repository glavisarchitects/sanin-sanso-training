# -*- coding: utf-8 -*-
{
    "name": "Purchase Order",
    "summary": """
        Purchase Order
    """,
    "version": "14.0.1.0.0",
    "category": "Purchase",
    "depends": [
        "x_purchase_quotation"
    ],
    "data": [
        # SECURITY
        "security/purchase_security.xml",
        "security/ir.model.access.csv",
        "security/purchase_rule.xml",
        # DATA
        # VIEWS
        "views/product_template_views.xml",
        "views/purchase_views.xml",
        "views/res_config_settings_views.xml",
        # WIZARDS
        "wizards/purchase_confirm_wiz_view.xml",
        # REPORTS
        "reports/purchase_order_template_report.xml",
        "reports/action.xml",
        # MAIL TEMPLATE
        "data/mail_template_data.xml",
    ],
    "application": False,
    "installable": True,
}
