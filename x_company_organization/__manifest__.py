{
    "name": "Company Organization",
    "summary":
    """
    Multiple Branches, Teams and Organizations Management
    """,
    "description":
"""
What it does
============


Supported Editions
==================

1. Community Edition.
2. Enterprise Edition.
""",
    "author": "SystemGear Viet Nam",
    "version": "14.0.0.1.0",
    "category": "Human Resources/Employees",
    "license": "OPL-1",
    "depends": [
        "sale_purchase_stock",
        "hr"
    ],
    "data": [
        # DATA
        "data/x_company_organization_data.xml",
        # SECURITY
        "security/x_company_organization_security.xml",
        "security/ir.model.access.csv",
        # VIEWS
        "views/hr_employee_views.xml",
        "views/res_company_views.xml",
        "views/res_organization_category_views.xml",
        "views/res_organization_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
