# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_連絡先",
    "summary": """
        山陰酸素工業　連絡先カスタマイズ
    """,
    "version": "14.0.1.1",
    "depends": [
        "base", "contacts", "calendar", "mail", "mrp_subcontracting"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # DATA
        'data/contact_category_data.xml',

        # VIEW
        'views/ss_erp_contact_category_views.xml',
        'views/res_partner_views.xml',
        'views/res_partner_bank_views.xml',
        'views/res_partner_form_views.xml',
        'views/ss_erp_partner_construction_views.xml',
        'views/ss_erp_partner_performance_views.xml',
        'views/webclient_templates.xml',

    ],
    "post_init_hook": "post_init_hook",
    "application": False,
    "installable": True,
}
