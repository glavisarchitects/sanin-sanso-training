# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_SVF",
    "summary": """
        山陰酸素工業　SVF統合カスタマイズ
    """,
    "depends": [
        "ss_erp_res_partner", "ss_erp_product_template", "ss_erp_organization",
        "ss_erp_responsible_dept", "ss_erp_res_company", "ss_erp_res_users",
        "ss_erp_external_data_import", "ss_erp_bank_fb", "ss_erp_accounting"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        'views/account_move_views.xml',

        'menu/menu_item.xml',

        # DATA
        'data/svf_cloud_config_data.xml',
    ],
    "application": False,
    "installable": True,
}
