# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_SuperStream連携",
    "summary": """
        山陰酸素工業　SuperStream連携カスタマイズ
    """,
    "depends": [
        "base", "ss_erp_stock", "ss_erp_accounting", "base_automation"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # DATA
        'data/param_data.xml',
        'data/update_linkage.xml',

        # VIEWS

        'views/ss_erp_inventory_order_views.xml',
        'views/ss_erp_account_move_line_views.xml',
        'views/ss_erp_superstream_linkage_journal_views.xml',
        'wizards/sstream_journal_entry_output_views.xml',
        'wizards/sstream_payment_journal_export_views.xml',

        # Menu
        'menu/menu_item.xml',
    ],
    "application": False,
    "installable": True,
}
