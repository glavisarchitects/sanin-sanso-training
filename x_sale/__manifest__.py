# -*- coding: utf-8 -*-
{
    'name': "x_sale",

    'summary': """summary desc""",

    'description': """Long description of module's purpose""",

    'author': "SGVN",
    'website': "http://www.yourcompany.com",
    
    'category': 'Uncategorized',
    
    'version': '0.1',

    'depends': ['base','sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
}
