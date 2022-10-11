#-*- coding:utf-8 -*-

{
    'name': 'Chilean Payslip Report',
    'category': 'Human Resources',
    'summary': """Manage your employee payroll reporting""",
    'version': '1.1',
    'sequence': 5,
    'description': """
Chilean Payslip Report
=======================
    * Print employee Chilean Payslip Report (Excel).
    """,
    'author': 'Konos',
    'website': 'https://www.konos.cl',
    'category': 'Localization',
    'depends': ['l10n_cl_hr'],
    'license': 'OPL-1',
    'data': [
        'security/ir.model.access.csv',
        'wizard/attachment_report_view.xml',
        'views/hr_payslip_view.xml',
    ],
    'images': ['static/description/banner.png'],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
