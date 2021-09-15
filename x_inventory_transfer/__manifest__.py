# -*- coding: utf-8 -*-
{
    'name': "X Inventory Transfer",

    'summary': """
            X Inventory Transfer""",

    'description': """
           X Inventory Transfer
    """,


    'author': "Systemgear Vietnam",
    'website': "https://www.systemgear-vietnam.com/",

    # any module necessary for this one to work correctly
    'depends': ['stock','x_company_organization'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_views.xml',
        'data/transfer_sequence_data.xml',
        'data/dispatch_data.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
}
