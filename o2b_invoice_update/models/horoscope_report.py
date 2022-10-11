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

from odoo import api, fields, models,_
from odoo.tools.misc import format_date
from odoo.exceptions import UserError, ValidationError

from dateutil.relativedelta import relativedelta
from itertools import chain

class HoroscopeReport(models.Model):
    _name = 'horoscope.report'
    _description = 'Horoscope Sales'
    _inherit = "account.aged.partner"
    _auto = False

    @api.model
    def _get_options(self, previous_options=None):
        # OVERRIDE
        options = super(HoroscopeReport, self)._get_options(previous_options=previous_options)
        options['filter_account_type'] = 'receivable'
        return options

    @api.model
    def _get_report_name(self):
        return _("Horóscopo Ventas")

    @api.model
    def _get_templates(self):
        # OVERRIDE
        templates = super(HoroscopeReport, self)._get_templates()
        templates['line_template'] = 'account_reports.line_template_aged_receivable_report'
        return templates

class HoroscopeReportVendors(models.Model):
    _name = 'horoscope.report.vendors'
    _description = 'Horoscope Vendor'
    _inherit = "account.aged.partner"
    _auto = False

    @api.model
    def _get_options(self, previous_options=None):
        # OVERRIDE
        options = super(HoroscopeReportVendors, self)._get_options(previous_options=previous_options)
        options['filter_account_type'] = 'payable'
        return options

    @api.model
    def _get_report_name(self):
        return _("Horóscopo Vendor")

    @api.model
    def _get_templates(self):
        # OVERRIDE
        templates = super(HoroscopeReportVendors, self)._get_templates()
        templates['line_template'] = 'account_reports.line_template_aged_payable_report'
        return templates

