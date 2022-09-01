# -*- coding: utf-8 -*-
{
    "name": "山陰酸素工業_外部データ取込",
    "summary": """
        山陰酸素工業　外部データ取込カスタマイズ
    """,
    "depends": [
        "sale", "purchase",
    ],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        'views/ss_erp_code_convert.xml',
        'views/ss_erp_convert_code_type.xml',
        'views/ss_erp_external_system_type.xml',
        'views/ss_erp_ifdb_autogas_file_data_rec_views.xml',
        'views/ss_erp_ifdb_autogas_file_header_views.xml',
        'views/ss_erp_ifdb_powernet_sales_detail_views.xml',
        'views/ss_erp_ifdb_powernet_sales_header_views.xml',
        'views/ss_erp_ifdb_propane_sales_detail_views.xml',
        'views/ss_erp_ifdb_propane_sales_header_views.xml',
        'views/ss_erp_ifdb_yg_detail_views.xml',
        'views/ss_erp_ifdb_yg_header_views.xml',
        'views/ss_erp_ifdb_yg_summary_views.xml',
        'views/ss_erp_youki_kanri_detail_views.xml',
        'views/ss_erp_youki_kanri_views.xml',
        'views/ss_erp_youki_kensa_views.xml',
        'views/webclient_templates.xml',
        'menu/menu_item.xml',

        # DATA
        # 'data/ir_action_server_data.xml',
        'data/parameter_config_data.xml',
        # 'data/ss_erp_convert_code_type_data.xml',
        'data/ss_erp_external_system_type_data.xml',
        'data/yamasan_product_data.xml',
    ],
    "application": False,
    "installable": True,
    'qweb': [
        'static/src/xml/import_custom.xml',
    ],
}
