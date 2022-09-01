# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_プロダクト",
    "summary": """
        山陰酸素工業　プロダクトカスタマイズ
    """,
    "depends": [
        "base", "account", "mail", "stock", "contacts", "contacts_enterprise",
        "sale", "purchase", "delivery", "uom"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # DATA
        'data/product_medium_classification_data.xml',
        'data/product_pricelist_class_data.xml',
        'data/uom_data.xml',
        'data/down_payment_product_data.xml',

        # VIEW
        'views/product_product_views.xml',
        'views/product_template_views.xml',
        'views/product_template_form_views.xml',
        'views/ss_erp_product_detail_classification_views.xml',
        'views/ss_erp_product_major_classification_views.xml',
        'views/ss_erp_product_medium_classification_views.xml',
        'views/ss_erp_product_minor_classification_views.xml',
        'views/ss_erp_product_price_views.xml',
        'views/ss_erp_product_pricelist_class_views.xml',

        # MENU
        'menu/menu_item.xml',

    ],
    "application": False,
    "installable": True,
}
