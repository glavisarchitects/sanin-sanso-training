# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_販売",
    "summary": """
        山陰酸素工業　販売管理カスタマイズ
    """,
    "depends": [
        "sale_management", "ss_erp_res_partner", "ss_erp_product_template"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        'views/sale_order_views.xml',

        # DATA
        'data/default_param_setting_data.xml',
        'data/menu_item.xml',
    ],
    "application": False,
    "installable": True,
}
