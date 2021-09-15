{
    "name": "Partner",
    "version": "14.0.0.1.0",
    "description": 
    """
    """,
    "summary": "Custom Partner for GA projects",
    "author": "SystemGear VietNam",
    "website": "",
    "license": "OPL-1",
    "depends": [
        "x_company_organization",
        "contacts",
    ],
    "data": [
        "data/x_partner_data.xml",
        "security/ir.model.access.csv",
        "views/res_partner_bank_views.xml",
        "views/res_partner_views.xml",
    ],
    "auto_install": False,
    "application": False,
}
