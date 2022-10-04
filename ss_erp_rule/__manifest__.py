# -*- coding: utf-8 -*-
{
    'name': "山陰酸素工業 規則",

    'summary': """
        山陰酸素工業 規則""",

    'description': """
        山陰酸素工業 規則
    """,
    # any module necessary for this one to work correctly
    'depends': ['ss_erp_accounting','ss_erp_construction','ss_erp_organization','ss_erp_product_template',
                'ss_erp_organization','ss_erp_res_partner','ss_erp_stock','ss_erp_responsible_dept',
                'ss_erp_external_data_import','ss_erp_bank_fb'],

    # always loaded
    'data': [
        "security/groups_security.xml",
        "security/menu_groups.xml",
        "security/view_groups.xml",
        'security/ir.model.access.csv',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
