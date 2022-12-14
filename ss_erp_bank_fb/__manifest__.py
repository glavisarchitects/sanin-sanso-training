# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_全銀Fb",
    "summary": """
        山陰酸素工業　全銀Fbカスタマイズ
    """,
    "depends": [
        "account_accountant","ss_erp_organization"
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # Data
        'data/param_data.xml',

        # VIEWS
        "views/web_assets.xml",
        'views/ss_erp_account_transfer_result_header_views.xml',
        'views/ss_erp_account_transfer_result_line_views.xml',
        'views/ss_erp_account_receipt_notification_header_views.xml',
        'views/ss_erp_account_receipt_notification_line_views.xml',



        # WIZARD
        'wizards/comprehensive_create_zengin_fb_wizard_views.xml',
        'wizards/zengin_account_transfer_request_fb_wizard_views.xml',

        'menu/menu_item.xml',
    ],
    "application": False,
    "installable": True,
    'qweb': [
        'static/src/xml/import_custom.xml',
        'static/src/xml/transfer_fb_buttons.xml',
    ],
}
