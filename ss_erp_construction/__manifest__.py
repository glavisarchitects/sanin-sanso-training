# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_工事",
    "summary": """
        山陰酸素工業　工事管理カスタマイズ
    """,
    "depends": [
        "ss_erp_res_partner", "ss_erp_product_template", "ss_erp_organization",
        "ss_erp_responsible_dept", "ss_erp_res_company", "ss_erp_res_users",
        "ss_erp_approval", "stock", "purchase", "account"

    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        'wizards/construction_make_invoice_advance_views.xml',
        'views/construction_template.xml',
        'views/construction_view.xml',
        'views/construction_workcenter.xml',
        'views/construction_workorder_view.xml',
        'views/approval_category_views.xml',
        'views/approval_request_view.xml',
        'views/stock_picking_views.xml',
        'views/construction_category_view.xml',
        'menu/menu_item.xml',

        # DATA
        'data/ir_sequence_data.xml',
    ],
    "application": False,
    "installable": True,
}
