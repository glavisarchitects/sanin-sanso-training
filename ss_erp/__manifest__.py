# -*- coding: utf-8 -*-
{
    "name": "SANNIN SANSO DUNK",
    "summary": """
        SANNIN SANSO DUNK
    """,
    "version": "14.0.1",
    "category": "",
    "website": "https://www.systemgear-vietnam.com/",
    "author": "SGVN",
    "depends": [
                "delivery","mail", "contacts", "purchase", "purchase_stock", "web"
                ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",
        "security/x_security_groups_security.xml",

        # DATA
        "data/bis_category_data.xml",
        "data/ir_sequence_data.xml",

        # REPORTS
        "reports/paperformat.xml",

        "reports/layout.xml",

        "reports/purchase_order_template_report.xml",
        # "reports/purchase_quotation_for_construction_report.xml",
        "reports/purchase_quotation_report.xml",
        "reports/action.xml",

        # VIEWS
        "views/organization_category_views.xml",
        "views/organization_views.xml",
        "views/partner_rebate_views.xml",
        "views/product_template_views.xml",
        "views/purchase_order_views.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "views/res_users_views.xml",
        "views/responsible_department_views.xml",
        "views/ss_erp_bis_category_views.xml",
        "views/stock_picking_views.xml",
        "views/web_access_rule_buttons.xml",
        "views/webclient_templates.xml",

        # Wizard
        "wizards/partner_rebate_attachment_wizard_views.xml",

        "data/mail_template_data.xml",

    ],
    "application": False,
    "installable": True,

}
