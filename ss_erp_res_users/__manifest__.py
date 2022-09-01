# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_ユーザ",
    "summary": """
        山陰酸素工業　ユーザカスタマイズ
    """,
    "depends": [
        "base", "ss_erp_organization", "auth_totp"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        'views/res_users_views.xml',
        'menu/menu_item.xml'
    ],
    "application": False,
    "installable": True,
}
