# -*- coding: utf-8 -*-
{
    "name": "Code Base",
    "summary": """
        Code Base
    """,
    "version": "14.0.1.0.0",
    "category": "Purchase",
    "depends": [
        "x_company_organization", "x_partner"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",
        # DATA
        # VIEWS
        "views/web_access_rule_buttons.xml",
        # REPORTS
        "reports/layout.xml",
        "reports/paperformat.xml",
        "views/transaction_classification_views.xml"
    ],
    "application": False,
    "installable": True,
    'pre_init_hook': 'pre_init_hook',
    'uninstall_hook': 'uninstall_hook',

}
