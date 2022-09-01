# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_従業員 ",
    "summary": """
        山陰酸素工業　従業員管理カスタマイズ
    """,
    "depends": [
        "ss_erp_res_partner", "ss_erp_product_template", "ss_erp_organization",
        "ss_erp_responsible_dept", "ss_erp_res_company", "ss_erp_res_users", "hr"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        'views/hr_employee_views.xml',
        'menu/menu_item.xml',

        # DATA
        'data/default_param_setting_data.xml',
    ],
    "application": False,
    "installable": True,
}
