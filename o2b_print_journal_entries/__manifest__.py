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
    'name': 'Print Journal Entries',
    'version': '14.0.0.0',
    'category': 'Account',
    'summary': 'Print Journal Entries.',
    'description': """
    Print Journal Entries
""",
    
    'author': 'O2B Technologies Pvt. Ltd.',
    'website': 'http://www.o2btechnologies.com',
    'depends': ['base','account'],
    'data': [
            'report/report_journal_entries.xml',
            'report/report_journal_entries_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
