{
    "name": "Company Organization",
    "summary":
    """
    Multiple Branches, Teams and Organizations Management
    """,
    "description":
    """
    """,
    "author": "SystemGear Viet Nam",
    "version": "14.0.0.1.0",
    "category": "Human Resources/Employees",
    "license": "OPL-1",
    "depends": [
        "sale_purchase_stock",
        "hr",
        "x_security_groups",
    ],
    "data": [
        # DATA
        "data/x_company_organization_data.xml",
        # SECURITY
        "security/ir.model.access.csv",
        # VIEWS
        "views/hr_employee_views.xml",
        "views/res_company_views.xml",
        "views/res_organization_category_views.xml",
        "views/res_organization_views.xml",
        "views/res_users_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
