# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_承認",
    "summary": """
        山陰酸素工業　承認管理カスタマイズ
    """,
    "depends": [
        "ss_erp_res_partner", "ss_erp_product_template", "ss_erp_organization",
        "ss_erp_responsible_dept", "ss_erp_res_company", "ss_erp_res_users",
        "ss_erp_sale", "ss_erp_purchase", "ss_erp_stock", "approvals"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # Data
        'data/mail_template_data.xml',

        # VIEWS
        'views/approval_category_views.xml',
        'views/approval_lost_views.xml',
        'views/approval_request_views.xml',
        'views/ss_erp_multi_approvers_views.xml',
        'views/webclient_templates.xml',
        'menu/menu_item.xml',

        # DATA
        'data/mail_template_data.xml'
    ],
    "application": False,
    "installable": True,
}
