# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_在庫",
    "summary": """
        山陰酸素工業　在庫カスタマイズ
    """,
    "depends": ["mail", "stock", "delivery", "ss_erp_product_template", "ss_erp_organization","ss_erp_res_users"],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        'views/webclient_templates.xml',
        'views/organization_views.xml',
        'views/ss_erp_instruction_order_line_views.xml',
        'views/ss_erp_instruction_order_views.xml',
        'views/ss_erp_inventory_order_views.xml',
        'views/ss_erp_lpgas_order_views.xml',
        'views/stock_inventory_line_views.xml',
        'views/stock_inventory_views.xml',
        'views/stock_location_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_scrap.xml',
        'views/ss_erp_stock_scrap_category_views.xml',
        'menu/menu_item.xml',

        # DATA
        'data/ir_action_server_data.xml',
        'data/ir_sequence_data.xml',
        # 'data/default_param_setting_data.xml',
    ],
    "application": False,
    "installable": True,
    'qweb': [
        'static/src/xml/instruction_detail.xml',
        'static/src/xml/instruction_view.xml',
    ],
}
