# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_購買",
    "summary": """
        山陰酸素工業　購買管理カスタマイズ
    """,
    "depends": [
        "purchase", "ss_erp_res_partner", "ss_erp_product_template", "ss_erp_organization",
        "ss_erp_responsible_dept", "ss_erp_res_company", "ss_erp_res_users", "account", "stock_dropshipping"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        'views/partner_rebate_views.xml',
        'views/purchase_order_views.xml',
        'views/ss_erp_bis_category_views.xml',
        'views/account_move_views.xml',
        'wizards/partner_rebate_attachment_wizard_views.xml',
        'menu/menu_item.xml',

        # REPORTS
        "reports/paperformat.xml",
        "reports/layout.xml",
        "reports/purchase_order_template_report.xml",
        "reports/purchase_quotation_report.xml",
        "reports/action.xml",

        # DATA
        'data/partner_rebate_sequence_data.xml',
        'data/bis_category_data.xml',
        'data/ir_sequence_data.xml',
        # 'data/default_param_setting_data.xml',
    ],
    "application": False,
    "installable": True,
}
