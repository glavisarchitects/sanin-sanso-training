# -*- coding: utf-8 -*-
{
    "name": "SGVN Rebate Management",
    "summary": """
        SGVN Rebate Management
    """,
    "version": "14.0.1.0.0",
    "category": "Purchase",
    "website": "https://www.systemgear-vietnam.com/",
    "author": "SGVN",
    "depends": [
        "ss_erp_master",
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",
        # "security/rebate_security.xml",
        # DATA
        "data/ir_sequence_data.xml",
        # VIEWS
        "views/partner_rebate_views.xml",
        # "views/webclient_templates.xml",
        # WIZARDS
        "wizards/partner_rebate_attachment_wizard_views.xml",
        # REPORTS

    ],
    "application": False,
    "installable": True,
}
