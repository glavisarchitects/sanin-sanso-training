# -*- coding: utf-8 -*-
{
    "name": "SS ERP Master",
    "summary": """
        SS ERP Master
    """,
    "version": "14.0.1.0.0",
    "category": "",
    "depends": [
        "mail"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",
        # DATA
        # VIEWS
        "views/responsible_department_views.xml",
        "views/organization_views.xml",
        "views/organization_category_views.xml",
        # REPORTS

    ],
    "application": False,
    "installable": True,
}
