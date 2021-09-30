# -*- coding: utf-8 -*-
{
    "name": "Rebate Management",
    "summary": """
        Rebate Management
    """,
    "version": "14.0.1.0.0",
    "category": "Purchase",
    "depends": [
        "x_company_organization", "x_partner", "purchase", "account"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",
        "security/rebate_security.xml",
        # DATA
        "data/ir_sequence_data.xml",
        # VIEWS
        "views/partner_rebate_views.xml",
        "views/webclient_templates.xml",
        # WIZARDS
        "wizards/partner_rebate_attachment_wizard_views.xml",
        # REPORTS

    ],
    "application": False,
    "installable": True,
}
