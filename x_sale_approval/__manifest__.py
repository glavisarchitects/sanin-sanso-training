# -*- coding: utf-8 -*-
{
    'name': "x_sale_approval",
    'summary': """Sale Approval""",
    'description': """Sale Approval""",
    'author': "SGVN",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'sale', 'x_company_organization'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'winzards/sale_quotation_approval_winzard.xml',
        'winzards/sale_order_approval_winzard.xml',
    ],
}
