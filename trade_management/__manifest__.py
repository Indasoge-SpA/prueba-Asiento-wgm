# -*- coding: utf-8 -*-
{
    'name': "trade_management",

    'summary': "Trade Management Module",


    'description': """
        Trade Management Module, helps control the information and state of imports
    """,

    'author': "Indasoge",
    'website': "http://www.indasoge.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory/Purchase',
    'version': '14.0.0.7',

    # any module necessary for this one to work correctly
    'depends': ['purchase','mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/origins_destinations.xml',
        'views/shipment_menu_items.xml',
        'views/shipment_views.xml',
        'views/shipment_origin_views.xml',
        'views/shipment_dest_port_views.xml',
        'views/containers_views.xml',
        'views/purchase_views_inherit.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
