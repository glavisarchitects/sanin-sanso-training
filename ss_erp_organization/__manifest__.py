# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_組織",
    "summary": """
        山陰酸素工業　組織カスタマイズ
    """,
    "depends": [
        "base", "mail"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        'views/organization_category_views.xml',
        'views/organization_views.xml',
        'menu/menu_item.xml'
    ],
    "application": False,
    "installable": True,
}
