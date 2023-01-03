# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_従業員 ",
    "summary": """
        山陰酸素工業　従業員管理カスタマイズ
    """,
    "depends": [
        "hr", "ss_erp_organization","hr_contract",
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        'views/hr_employee_views.xml',
        'views/hr_employee_puclic_views.xml',
        'menu/menu_item.xml',
    ],
    "application": False,
    "installable": True,
}
