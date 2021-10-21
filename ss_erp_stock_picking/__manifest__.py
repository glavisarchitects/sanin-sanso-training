# -*- coding: utf-8 -*-
{
    "name": "SGVN Stock Picking",
    "summary": """
        SGVN Stock Picking
    """,
    "version": "14.0.1.0.0",
    "category": "Purchase",
    "website": "https://www.systemgear-vietnam.com/",
    "author": "SGVN",
    "depends": [
        "ss_erp_purchase", "delivery"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",
        # DATA
        # VIEWS
        "views/stock_picking_views.xml",
        # REPORTS
    ],
    "application": False,
    "installable": True,
}
