# -*- coding: utf-8 -*-
{
    'name': "Inventory Transfer",

    'summary': """
              Inventory Transfer""",

    'description': """
            Inventory Transfer
    """,

    'author': "SGVN",

    # any module necessary for this one to work correctly
    'depends': ['stock'],

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
