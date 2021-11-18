# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業",
    "summary": """
        山陰酸素工業
    """,
    "version": "14.0.1",
    "category": "",
    "website": "https://www.systemgear-vietnam.com/",
    "author": "SGVN",
    "depends": [
        "base", "delivery", "mail", "contacts", "purchase",
        "purchase_stock", "web", "account", "stock_dropshipping", "approvals", "hr",
        "approvals_purchase_stock",
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",
        "security/x_security_groups_security.xml",
        "data/contact_category_data.xml",''
        "security/approval_security.xml",

        # DATA
        "data/bis_category_data.xml",
        "data/ir_sequence_data.xml",
        "data/product_pricelist_class_data.xml",

        # REPORTS
        "reports/paperformat.xml",
        "reports/layout.xml",
        "reports/purchase_order_template_report.xml",
        "reports/purchase_quotation_report.xml",
        "reports/action.xml",

        # VIEWS
        "views/assets.xml",
        "views/organization_category_views.xml",
        "views/organization_views.xml",
        "views/partner_rebate_views.xml",
        "views/product_template_views.xml",
        "views/purchase_order_views.xml",
        "views/res_company_views.xml",
        "views/ss_erp_partner_performance_views.xml",
        "views/ss_erp_partner_construction_views.xml",
        "views/res_partner_views.xml",
        "views/res_users_views.xml",
        "views/responsible_department_views.xml",
        "views/ss_erp_bis_category_views.xml",
        "views/stock_picking_views.xml",
        "views/web_access_rule_buttons.xml",
        "views/res_partner_bank_views.xml",
        "views/ss_erp_contact_category_views.xml",
        "views/approval_category_views.xml",
        "views/approval_lost_views.xml",
        "views/approval_request_views.xml",
        "views/hr_employee_views.xml",
        "views/res_partner_form_views.xml",
        "views/ss_erp_multi_approvers_views.xml",
        "views/sale_order_views.xml",
        "views/ss_erp_subaccount_views.xml",
        "views/stock_scrap.xml",
        "views/ss_erp_product_price_views.xml",
        "views/ss_erp_product_pricelist_class_views.xml",

        # Wizard
        "wizards/partner_rebate_attachment_wizard_views.xml",

        "data/mail_template_data.xml",

    ],
    "application": False,
    "installable": True,
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",

}
