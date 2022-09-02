# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_管轄部門",
    "summary": """
        山陰酸素工業　管轄部門カスタマイズ
    """,
    "depends": [
        "base", "mail"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        'views/responsible_department_views.xml',
        'menu/menu_item.xml'
    ],
    "application": False,
    "installable": True,
}
