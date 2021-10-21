# -*- coding: utf-8 -*-
{
    "name": "SGVN Purchase",
    "summary": """
        SGVN Purchase Quotation
    """,
    "version": "14.0.1.0.0",
    "category": "Purchase",
    "website": "https://www.systemgear-vietnam.com/",
    "author": "SGVN",
    "depends": [
        "ss_erp_base", "ss_erp_master", "purchase_stock", "stock_dropshipping", "sales_team"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",
        # DATA
        # VIEWS
        "views/res_company_views.xml",
        "views/product_template_views.xml",
        "views/purchase_order_views.xml",
        "views/res_partner_views.xml",
        # REPORTS
        "reports/action.xml",
        # "reports/layout.xml",
        "reports/purchase_quotation_report.xml",
        "reports/purchase_quotation_for_construction_report.xml",
        "reports/purchase_order_template_report.xml",
        # # MAIL TEMPLATE
        "data/mail_template_data.xml",
    ],
    "application": False,
    "installable": True,
    'pre_init_hook': 'pre_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
