# -*- coding: utf-8 -*-
##########################################################################
# Author      : O2b Technologies Pvt. Ltd.(<www.o2btechnologies.com>)
# Copyright(c): 2016-Present O2b Technologies Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
##########################################################################

{
    "name": """o2b_invoice_update""",
    'version': '1.0.',
    'category': 'Uncategorized',
    'sequence': 12,
    'author':  'O2B Technologies Pvt. Ltd.',
    'description': """
                This module helps to move sale order field named as "official seller" information 
                to sales invoice with tracking.
    """,
    'website': 'http://www.o2btechnologies.com',
    'depends': ['sale', 'account', 'product', 'purchase', 'industry_fsm_sale',
                'account_reports','project','o2b_mobile_app', 'industry_fsm_report','hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_report.xml',
        'views/worksheet_report.xml',
        'views/invoice_report.xml',
        'views/view.xml',
    ],
}
