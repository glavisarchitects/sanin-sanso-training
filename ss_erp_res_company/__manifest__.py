# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_会社",
    "summary": """
        山陰酸素工業　会社カスタマイズ
    """,
    "depends": [
        "base", "base_import", "digest", "mail"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # DATA
        "data/default_param_setting_data.xml",
    ],
    "application": False,
    "installable": True,
}
