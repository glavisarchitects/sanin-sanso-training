# -*- coding: utf-8 -*-
{
    "name": "SGVN Base",
    "summary": """
        SGVN Base
    """,
    "version": "14.0.1.0.0",
    "category": "Purchase",
    "website": "https://www.systemgear-vietnam.com/",
    "author": "SGVN",
    "depends": [
        "mail",
        "ss_erp_master"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",
        # DATA
        # VIEWS
        # "views/web_access_rule_buttons.xml",
        # REPORTS
        "reports/layout.xml",
        "reports/paperformat.xml",

    ],
    "application": False,
    "installable": True,

}
