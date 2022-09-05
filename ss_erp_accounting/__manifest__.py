# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_会計",
    "summary": """
        山陰酸素工業　会計管理カスタマイズ
    """,
    "depends": [
        "account_accountant",
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        'views/account_move_line_view.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
        'views/ss_erp_bank_commission_view.xml',
        'views/ss_erp_subaccount_views.xml',
        'views/webclient_templates.xml',
        'views/ss_erp_petty_cash_note_view.xml',

        # WIZARD
        'wizards/account_invoice_list_history_views.xml',
        'wizards/account_list_receivable_views.xml',
        'wizards/account_receivable_balance_confirm_views.xml',
        'wizards/account_receivable_customer_ledger_views.xml',
        'wizards/account_register_payment_views.xml',

        # MENU
        'menu/menu_item.xml',

        # DATA
        # 'data/default_param_setting_data.xml',
    ],
    "application": False,
    "installable": True,
}