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
    "name"                 : "Customer Credit Limit Setup ",
    "summary"              : 'This Module checks customer credit limit and block customers that have invoices with more than 30 days overdued payment, before confirming sale order',
    "version"              : "14.0.1",
    "author"               : "O2b Technologies Pvt. Ltd.",
    "contributors"         : ['O2b Technologies <info@o2b.co.in>'],
    "website"              : 'https://www.o2btechnologies.com',
    "category"             : "Accounting",
    "depends"              : ['sale','account','mail','sale_stock', 'account_followup','base',
                                'o2b_invoice_update', 'project', 'industry_fsm'],
    "data"                 : [
                                   "security/ir.model.access.csv",
                                   "security/security.xml",
                                   "data/credit_limit_mail_template.xml",
                                   "wizard/customer_limit_wizard_view.xml",
                                   "views/partner_view.xml",
                                   "views/sale_order_view.xml",
                                   "views/field_service.xml",
                             ],
    "installable"          : True,
    "auto_install"         : False,
    "application"          : True,
    "license"              : "OPL-1",
    "price"                : 100,
    "currency"             : 'EUR',

}