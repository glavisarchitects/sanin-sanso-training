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
        'views/product_pricelist_view.xml',
        'wizards/sale_quotation_approval_wizard.xml'
    ],
}
