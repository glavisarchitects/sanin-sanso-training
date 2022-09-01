# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_販売",
    "summary": """
        山陰酸素工業　販売管理カスタマイズ
    """,
    "depends": [
        "ss_erp_res_partner", "ss_erp_product_template", "ss_erp_organization",
        "ss_erp_responsible_dept", "ss_erp_res_company", "ss_erp_res_users", "ss_erp_hr", "ss_erp_svf_intergration"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        'views/sale_order_views.xml',

        # DATA
        'data/default_param_setting_data.xml',
    ],
    "application": False,
    "installable": True,
}
