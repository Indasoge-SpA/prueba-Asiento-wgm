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
    "name": """o2b_split_invoice""",
    'version': '1.0.',
    'category': 'Uncategorized',
    'sequence': 12,
    'author':  'O2B Technologies Pvt. Ltd.',
    'description': """
                This module helps to provide information of invoice splitting.
    """,
    'website': 'http://www.o2btechnologies.com',
    'depends': ['sale', 'account'],
    'data': [
        'views/invoice.xml',
        'wizard/wiz_invoice.xml',
    ],
}
