# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_SVF",
    "summary": """
        山陰酸素工業　SVF統合カスタマイズ
    """,
    "depends": [
        "ss_erp_web","ss_erp_res_partner", "ss_erp_product_template", "ss_erp_organization",
        "ss_erp_responsible_dept", "ss_erp_res_company", "ss_erp_res_users",
        "ss_erp_external_data_import", "ss_erp_bank_fb", "ss_erp_accounting", "ss_erp_construction"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        'views/account_move_views.xml',
        'views/construction_view.xml',
        'views/purchase_order_views.xml',
        'views/sale_order_view.xml',
        'views/stock_picking_views.xml',

        # WIZARD
        'wizards/account_invoice_list_history_views.xml',
        'wizards/account_list_receivable_views.xml',
        'wizards/account_receivable_balance_confirm_views.xml',
        'wizards/account_receivable_customer_ledger_views.xml',
        'wizards/payment_vendor_notice_views.xml',


        'menu/menu_item.xml',

        # DATA
        'data/svf_cloud_config_data.xml',
    ],
    "application": False,
    "installable": True,
}
