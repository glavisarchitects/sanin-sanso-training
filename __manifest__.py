{
    "name": "Sale Approval",
    "summary":
"""
Quotation Approval before interacting with customer
""",
    "description":
"""
What it does
============

Quotation Approval before interacting with customer.

Supported Editions
==================

1. Community Edition.
2. Enterprise Edition.
""",
    "author": "SystemGear Viet Nam",
    "version": "14.0.0.1.0",
    "category": "Sales/Sales",
    "license": "OPL-1",
    "depends": [
        "sale"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
        "wizards/sale_order_request_approval_views.xml",
        "wizards/sale_order_response_approval_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
