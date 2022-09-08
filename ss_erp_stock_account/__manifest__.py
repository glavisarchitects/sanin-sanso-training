# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_在庫会計",
    "summary": """
        山陰酸素工業　在庫会計カスタマイズ
    """,
    "depends": [
        "ss_erp_accounting", "ss_erp_stock"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        'views/account_move_views.xml',
        'menu/menu_item.xml'
    ],
    "application": False,
    "installable": True,
}
