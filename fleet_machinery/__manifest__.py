# -*- coding: utf-8 -*-
{
    'name': "Fleet Machinery",

    'summary': """
        Add management information for machinery""",

    'description': """
        Add management information for machinery
        like hours used...
    """,

    'author': "Indasoge Spa",
    'website': "http://www.indasoge.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources/Fleet',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['fleet'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        #'views/fleet_views.xml',
    ],

    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    
}
