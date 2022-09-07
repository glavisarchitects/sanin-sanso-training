# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_製造",
    "summary": """
        山陰酸素工業　製造管理カスタマイズ
    """,
    "depends": [
        "ss_erp_res_partner", "ss_erp_product_template", "ss_erp_organization",
        "ss_erp_responsible_dept", "ss_erp_res_company", "ss_erp_res_users",
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        'menu/menu_item.xml'
    ],
    "application": False,
    "installable": True,
}
