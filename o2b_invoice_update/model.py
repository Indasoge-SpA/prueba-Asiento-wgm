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
import ast
import copy
import json
import io
import logging
import lxml.html
import datetime
import ast
from collections import defaultdict
from math import copysign

from dateutil.relativedelta import relativedelta

from odoo.tools.misc import xlsxwriter
from odoo import models, fields, api, _
from odoo.tools import config, date_utils, get_lang
from odoo.osv import expression
from babel.dates import get_quarter_names
from odoo.tools.misc import formatLang, format_date
from odoo.addons.web.controllers.main import clean_action

_logger = logging.getLogger(__name__)

from odoo.exceptions import UserError, ValidationError

from itertools import chain

class SaleOrder(models.Model):
    _inherit = "sale.order"

    x_studio_vendedor_oficial_1 = fields.Many2one('hr.employee', string = "Vendedor Oficial", tracking = True)
    
    def _create_invoices(self, grouped=False, final=False, date=None):
        res = super(SaleOrder,self)._create_invoices(grouped=False, final=False, date=None)
        res.x_studio_vendedor_oficial = self.x_studio_vendedor_oficial_1
        return res

class AccountMove(models.Model):
    _inherit = "account.move"

    x_studio_vendedor_oficial = fields.Many2one('hr.employee', string = "Vendedor Oficial", tracking = True)

class ProductProduct(models.Model):
    _inherit = "product.product"

    def get_product_multiline_description_sale(self):
        """ Compute a multiline description of this product, in the context of sales
                (do not use for purchases or other display reasons that don't intend to use "description_sale").
            It will often be used as the default description of a sale order line referencing this product.
        """
        name = ''
        if not self.description_sale:
            name = ' '+self.name
        if self.description_sale:
            if name:
                name += '\n' + self.description_sale
                # print()
            else:
                name += self.description_sale
        return name

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_computed_name(self):
        self.ensure_one()
        if not self.product_id:
            return ''
        if self.partner_id.lang:
            product = self.product_id.with_context(lang=self.partner_id.lang)
            name = ''
            if not product.description:
                name = ' '+product.name
            if product.description:
                if name:
                    name += '\n' + product.description
                else:
                    name += product.description
            return name
        else:
            product = self.product_id
        values = []
        if product.partner_ref:
            values.append(product.partner_ref)
        if self.journal_id.type == 'sale':
            if product.description_sale:
                values.append(product.description_sale)
        elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values.append(product.description_purchase)
        return '\n'.join(values)

class ReportAccountAgedPartner(models.AbstractModel):
    _inherit = "account.aged.partner"
    _order = "partner_name, invoice_date asc, report_date asc, move_name desc"

    invoice_date = fields.Date(group_operator='max', string='Invoice Issue Date')
    amount_residual = fields.Monetary(string='Amount Due')


    @api.model
    def _get_sql(self):
        if self._name == 'account.aged.receivable':
            options = self.env.context['report_options']
            query = ("""
                SELECT
                    {move_line_fields},
                    account_move_line.partner_id AS partner_id,
                    partner.name AS partner_name,
                    COALESCE(trust_property.value_text, 'normal') AS partner_trust,
                    COALESCE(account_move_line.currency_id, journal.currency_id) AS report_currency_id,
                    account_move_line.payment_id AS payment_id,
                    COALESCE(move.invoice_date, account_move_line.date) AS invoice_date,
                    move.amount_residual AS amount_residual,
                    COALESCE(account_move_line.date_maturity, account_move_line.date) AS report_date,
                    account_move_line.expected_pay_date AS expected_pay_date,
                    move.move_type AS move_type,
                    move.name AS move_name,
                    journal.code AS journal_code,
                    account.name AS account_name,
                    account.code AS account_code,""" + ','.join([("""
                    CASE WHEN period_table.period_index = {i}
                    THEN %(sign)s * ROUND((
                        account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0)
                    ) * currency_table.rate, currency_table.precision)
                    ELSE 0 END AS period{i}""").format(i=i) for i in range(6)]) + """
                FROM account_move_line
                JOIN account_move move ON account_move_line.move_id = move.id
                JOIN account_journal journal ON journal.id = account_move_line.journal_id
                JOIN account_account account ON account.id = account_move_line.account_id
                LEFT JOIN res_partner partner ON partner.id = account_move_line.partner_id
                LEFT JOIN ir_property trust_property ON (
                    trust_property.res_id = 'res.partner,'|| account_move_line.partner_id
                    AND trust_property.name = 'trust'
                    AND trust_property.company_id = account_move_line.company_id
                )
                JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN LATERAL (
                    SELECT part.amount, part.debit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <= %(date)s
                ) part_debit ON part_debit.debit_move_id = account_move_line.id
                LEFT JOIN LATERAL (
                    SELECT part.amount, part.credit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <= %(date)s
                ) part_credit ON part_credit.credit_move_id = account_move_line.id
                JOIN {period_table} ON (
                    period_table.date_start IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
                )
                AND (
                    period_table.date_stop IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
                )
                WHERE account.internal_type = %(account_type)s
                GROUP BY account_move_line.id, partner.id, trust_property.id, journal.id, move.id, account.id,
                         period_table.period_index, currency_table.rate, currency_table.precision
                HAVING ROUND(account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0), currency_table.precision) != 0
            """).format(
                move_line_fields=self._get_move_line_fields('account_move_line'),
                currency_table=self.env['res.currency']._get_query_currency_table(options),
                period_table=self._get_query_period_table(options),
            )
            params = {
                'account_type': options['filter_account_type'],
                'sign': 1 if options['filter_account_type'] == 'receivable' else -1,
                'date': options['date']['date_to'],
            }
            return self.env.cr.mogrify(query, params).decode(self.env.cr.connection.encoding)
        elif self._name == 'horoscope.report':
            # print("==== self ==== ")
            options = self.env.context['report_options']
            query = ("""
                SELECT
                    {move_line_fields},
                    account_move_line.partner_id AS partner_id,
                    partner.name AS partner_name,
                    COALESCE(trust_property.value_text, 'normal') AS partner_trust,
                    COALESCE(account_move_line.currency_id, journal.currency_id) AS report_currency_id,
                    account_move_line.payment_id AS payment_id,
                    COALESCE(move.invoice_date, account_move_line.date) AS invoice_date,
                    move.amount_residual AS amount_residual,
                    COALESCE(account_move_line.date_maturity, account_move_line.date) AS report_date,
                    account_move_line.expected_pay_date AS expected_pay_date,
                    move.move_type AS move_type,
                    move.name AS move_name,
                    journal.code AS journal_code,
                    account.name AS account_name,
                    account.code AS account_code,""" + ','.join([("""
                    CASE WHEN period_table.period_index = {i}
                    THEN %(sign)s * ROUND((
                        account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0)
                    ) * currency_table.rate, currency_table.precision)
                    ELSE 0 END AS period{i}""").format(i=i) for i in range(6)]) + """
                FROM account_move_line
                JOIN account_move move ON account_move_line.move_id = move.id
                JOIN account_journal journal ON journal.id = account_move_line.journal_id
                JOIN account_account account ON account.id = account_move_line.account_id
                LEFT JOIN res_partner partner ON partner.id = account_move_line.partner_id
                LEFT JOIN ir_property trust_property ON (
                    trust_property.res_id = 'res.partner,'|| account_move_line.partner_id
                    AND trust_property.name = 'trust'
                    AND trust_property.company_id = account_move_line.company_id
                )
                JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN LATERAL (
                    SELECT part.amount, part.debit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <= %(date)s
                ) part_debit ON part_debit.debit_move_id = account_move_line.id
                LEFT JOIN LATERAL (
                    SELECT part.amount, part.credit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <= %(date)s
                ) part_credit ON part_credit.credit_move_id = account_move_line.id
                JOIN {period_table} ON (
                    period_table.date_start IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
                )
                AND (
                    period_table.date_stop IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
                )
                WHERE account.internal_type = %(account_type)s AND journal.type = 'sale'
                GROUP BY account_move_line.id, partner.id, trust_property.id, journal.id, move.id, account.id,
                         period_table.period_index, currency_table.rate, currency_table.precision
                HAVING ROUND(account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0), currency_table.precision) != 0
            """).format(
                move_line_fields=self._get_move_line_fields('account_move_line'),
                currency_table=self.env['res.currency']._get_query_currency_table(options),
                period_table=self._get_query_period_table(options),
            )
            params = {
                'account_type': options['filter_account_type'],
                'sign': 1 if options['filter_account_type'] == 'receivable' else -1,
                'date': options['date']['date_to'],
            }
            return self.env.cr.mogrify(query, params).decode(self.env.cr.connection.encoding)
        elif self._name == 'horoscope.report.vendors':
            options = self.env.context['report_options']
            query = ("""
                SELECT
                    {move_line_fields},
                    account_move_line.partner_id AS partner_id,
                    partner.name AS partner_name,
                    COALESCE(trust_property.value_text, 'normal') AS partner_trust,
                    COALESCE(account_move_line.currency_id, journal.currency_id) AS report_currency_id,
                    account_move_line.payment_id AS payment_id,
                    COALESCE(move.invoice_date, account_move_line.date) AS invoice_date,
                    move.amount_residual AS amount_residual,
                    COALESCE(account_move_line.date_maturity, account_move_line.date) AS report_date,
                    account_move_line.expected_pay_date AS expected_pay_date,
                    move.move_type AS move_type,
                    move.name AS move_name,
                    journal.code AS journal_code,
                    account.name AS account_name,
                    account.code AS account_code,""" + ','.join([("""
                    CASE WHEN period_table.period_index = {i}
                    THEN %(sign)s * ROUND((
                        account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0)
                    ) * currency_table.rate, currency_table.precision)
                    ELSE 0 END AS period{i}""").format(i=i) for i in range(6)]) + """
                FROM account_move_line
                JOIN account_move move ON account_move_line.move_id = move.id
                JOIN account_journal journal ON journal.id = account_move_line.journal_id
                JOIN account_account account ON account.id = account_move_line.account_id
                LEFT JOIN res_partner partner ON partner.id = account_move_line.partner_id
                LEFT JOIN ir_property trust_property ON (
                    trust_property.res_id = 'res.partner,'|| account_move_line.partner_id
                    AND trust_property.name = 'trust'
                    AND trust_property.company_id = account_move_line.company_id
                )
                JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN LATERAL (
                    SELECT part.amount, part.debit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <= %(date)s
                ) part_debit ON part_debit.debit_move_id = account_move_line.id
                LEFT JOIN LATERAL (
                    SELECT part.amount, part.credit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <= %(date)s
                ) part_credit ON part_credit.credit_move_id = account_move_line.id
                JOIN {period_table} ON (
                    period_table.date_start IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
                )
                AND (
                    period_table.date_stop IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
                )
                WHERE account.internal_type = %(account_type)s AND journal.type = 'purchase'
                GROUP BY account_move_line.id, partner.id, trust_property.id, journal.id, move.id, account.id,
                         period_table.period_index, currency_table.rate, currency_table.precision
                HAVING ROUND(account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0), currency_table.precision) != 0
            """).format(
                move_line_fields=self._get_move_line_fields('account_move_line'),
                currency_table=self.env['res.currency']._get_query_currency_table(options),
                period_table=self._get_query_period_table(options),
            )
            params = {
                'account_type': options['filter_account_type'],
                'sign': 1 if options['filter_account_type'] == 'receivable' else -1,
                'date': options['date']['date_to'],
            }
            return self.env.cr.mogrify(query, params).decode(self.env.cr.connection.encoding)
        else:
            options = self.env.context['report_options']
            query = ("""
                SELECT
                    {move_line_fields},
                    account_move_line.partner_id AS partner_id,
                    partner.name AS partner_name,
                    COALESCE(trust_property.value_text, 'normal') AS partner_trust,
                    COALESCE(account_move_line.currency_id, journal.currency_id) AS report_currency_id,
                    account_move_line.payment_id AS payment_id,
                    COALESCE(move.invoice_date, account_move_line.date) AS invoice_date,
                    move.amount_residual AS amount_residual,
                    COALESCE(account_move_line.date_maturity, account_move_line.date) AS report_date,
                    account_move_line.expected_pay_date AS expected_pay_date,
                    move.move_type AS move_type,
                    move.name AS move_name,
                    journal.code AS journal_code,
                    account.name AS account_name,
                    account.code AS account_code,""" + ','.join([("""
                    CASE WHEN period_table.period_index = {i}
                    THEN %(sign)s * ROUND((
                        account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0)
                    ) * currency_table.rate, currency_table.precision)
                    ELSE 0 END AS period{i}""").format(i=i) for i in range(6)]) + """
                FROM account_move_line
                JOIN account_move move ON account_move_line.move_id = move.id
                JOIN account_journal journal ON journal.id = account_move_line.journal_id
                JOIN account_account account ON account.id = account_move_line.account_id
                LEFT JOIN res_partner partner ON partner.id = account_move_line.partner_id
                LEFT JOIN ir_property trust_property ON (
                    trust_property.res_id = 'res.partner,'|| account_move_line.partner_id
                    AND trust_property.name = 'trust'
                    AND trust_property.company_id = account_move_line.company_id
                )
                JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN LATERAL (
                    SELECT part.amount, part.debit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <= %(date)s
                ) part_debit ON part_debit.debit_move_id = account_move_line.id
                LEFT JOIN LATERAL (
                    SELECT part.amount, part.credit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <= %(date)s
                ) part_credit ON part_credit.credit_move_id = account_move_line.id
                JOIN {period_table} ON (
                    period_table.date_start IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
                )
                AND (
                    period_table.date_stop IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
                )
                WHERE account.internal_type = %(account_type)s
                GROUP BY account_move_line.id, partner.id, trust_property.id, journal.id, move.id, account.id,
                         period_table.period_index, currency_table.rate, currency_table.precision
                HAVING ROUND(account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0), currency_table.precision) != 0
            """).format(
                move_line_fields=self._get_move_line_fields('account_move_line'),
                currency_table=self.env['res.currency']._get_query_currency_table(options),
                period_table=self._get_query_period_table(options),
            )
            params = {
                'account_type': options['filter_account_type'],
                'sign': 1 if options['filter_account_type'] == 'receivable' else -1,
                'date': options['date']['date_to'],
            }
            return self.env.cr.mogrify(query, params).decode(self.env.cr.connection.encoding)

    ####################################################
    # COLUMNS/LINES
    ####################################################
    @api.model
    def _get_column_details(self, options):
        if self._name == 'account.aged.receivable':
            return [
                self._header_column(),
                self._field_column('invoice_date'),
                self._field_column('report_date'),
                self._field_column('journal_code', name=_("Journal")),
                self._field_column('account_name', name=_("Account")),
                self._field_column('expected_pay_date'),
                self._field_column('period0', name=_("As of: %s") % format_date(self.env, options['date']['date_to'])),
                self._field_column('period1', sortable=True),
                self._field_column('period2', sortable=True),
                self._field_column('period3', sortable=True),
                self._field_column('period4', sortable=True),
                self._field_column('period5', sortable=True),
                self._custom_column(  # Avoid doing twice the sub-select in the view
                    name=_('Total'),
                    classes=['number'],
                    formatter=self.format_value,
                    getter=(lambda v: v['period0'] + v['period1'] + v['period2'] + v['period3'] + v['period4'] + v['period5']),
                    sortable=True,
                ),
            ]
        elif self._name in ['horoscope.report', 'horoscope.report.vendors']:
            # print("self -----")
            return [
                self._header_column(),
                self._field_column('invoice_date'),
                # self._field_column('report_date'),
                # self._field_column('journal_code', name=_("Journal")),
                # self._field_column('account_name', name=_("Account")),
                # self._field_column('expected_pay_date'),
                self.with_context(hide_data=True)._field_column('period0', name=_("As of: %s") % format_date(self.env, options['date']['date_to'])),
                self.with_context(hide_data=True)._field_column('period1', sortable=True),
                self.with_context(hide_data=True)._field_column('period2', sortable=True),
                self.with_context(hide_data=True)._field_column('period3', sortable=True),
                self.with_context(hide_data=True)._field_column('period4', sortable=True),
                self.with_context(hide_data=True)._field_column('period5', sortable=True),
                # self.with_context(get_colspan_data_new=True)._field_column('amount_residual'),
                self.with_context(get_colspan_data_new=True)._custom_column(  # Avoid doing twice the sub-select in the view
                    name=_('Amount Due'),
                    formatter=self.format_value,
                    getter=(lambda v: v['period0'] + v['period1'] + v['period2'] + v['period3'] + v['period4'] + v['period5']),
                    sortable=True,
                ),
                # self._field_column('amount_residual', sortable=True),
                self.with_context(get_colspan_data=True)._custom_column(  # Avoid doing twice the sub-select in the view
                    name=_('Total'),
                    classes=['number', 'd-none'],
                    formatter=self.format_value,
                    getter=(lambda v: v['period0'] + v['period1'] + v['period2'] + v['period3'] + v['period4'] + v['period5']),
                    sortable=True,
                ),
            ]
        else:
            return [
                self._header_column(),
                self._field_column('report_date'),
                self._field_column('journal_code', name=_("Journal")),
                self._field_column('account_name', name=_("Account")),
                self._field_column('expected_pay_date'),
                self._field_column('period0', name=_("As of: %s") % format_date(self.env, options['date']['date_to'])),
                self._field_column('period1', sortable=True),
                self._field_column('period2', sortable=True),
                self._field_column('period3', sortable=True),
                self._field_column('period4', sortable=True),
                self._field_column('period5', sortable=True),
                self._custom_column(  # Avoid doing twice the sub-select in the view
                    name=_('Total'),
                    classes=['number'],
                    formatter=self.format_value,
                    getter=(lambda v: v['period0'] + v['period1'] + v['period2'] + v['period3'] + v['period4'] + v['period5']),
                    sortable=True,
                ),
            ]

class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    @api.model
    def _query_get(self, options, domain=None):
        domain = self._get_options_domain(options) + (domain or [])
        self.env['account.move.line'].check_access_rights('read')

        if self._name == 'account.check.receivable.report' or self._name == 'account.check.protested.report':
            domain += [('full_reconcile_id', '=', False), ('balance', '!=', 0), ('account_id.reconcile', '=', True)]
        query = self.env['account.move.line']._where_calc(domain)

        # Wrap the query with 'company_id IN (...)' to avoid bypassing company access rights.
        self.env['account.move.line']._apply_ir_rules(query)

        return query.get_sql()

    def get_xlsx(self, options, response=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {
            'in_memory': True,
            'strings_to_formulas': False,
        })
        sheet = workbook.add_worksheet(self._get_report_name()[:31])

        date_default_col1_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2, 'num_format': 'yyyy-mm-dd'})
        date_default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})
        default_col1_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})
        level_0_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 6, 'font_color': '#666666'})
        level_1_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 1, 'font_color': '#666666'})
        level_2_col1_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_2_col1_total_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_2_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_3_col1_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        level_3_col1_total_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_3_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})

        #Set the first column width to 50
        sheet.set_column(0, 0, 50)

        y_offset = 0
        headers, lines = self.with_context(no_format=True, print_mode=True, prefetch_fields=False)._get_table(options)

        # Add headers.
        if self._name in ['horoscope.report', 'horoscope.report.vendors']:
            for header in headers:
                x_offset = 0
                for column in header:
                    if column and column.get('name') not in ['1 - 30', '31 - 60', '61 - 90', '91 - 120', 'Older'] and 'As of:' not in column.get('name') and 'Al:' not in column.get('name'):
                        column_name_formated = column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
                        colspan = column.get('colspan', 1)
                        if colspan == 1:
                            sheet.write(y_offset, x_offset, column_name_formated, title_style)
                        else:
                            sheet.merge_range(y_offset, x_offset, y_offset, x_offset + colspan - 1, column_name_formated, title_style)
                        x_offset += colspan
                y_offset += 1
        else:
            for header in headers:
                x_offset = 0
                for column in header:
                    column_name_formated = column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
                    colspan = column.get('colspan', 1)
                    if colspan == 1:
                        sheet.write(y_offset, x_offset, column_name_formated, title_style)
                    else:
                        sheet.merge_range(y_offset, x_offset, y_offset, x_offset + colspan - 1, column_name_formated, title_style)
                    x_offset += colspan
                y_offset += 1

        if options.get('hierarchy'):
            lines = self._create_hierarchy(lines, options)
        if options.get('selected_column'):
            lines = self._sort_lines(lines, options)

        # Add lines.
        for y in range(0, len(lines)):
            level = lines[y].get('level')
            if lines[y].get('caret_options'):
                style = level_3_style
                col1_style = level_3_col1_style
            elif level == 0:
                y_offset += 1
                style = level_0_style
                col1_style = style
            elif level == 1:
                style = level_1_style
                col1_style = style
            elif level == 2:
                style = level_2_style
                col1_style = 'total' in lines[y].get('class', '').split(' ') and level_2_col1_total_style or level_2_col1_style
            elif level == 3:
                style = level_3_style
                col1_style = 'total' in lines[y].get('class', '').split(' ') and level_3_col1_total_style or level_3_col1_style
            else:
                style = default_style
                col1_style = default_col1_style

            #write the first column, with a specific style to manage the indentation
            cell_type, cell_value = self._get_cell_type_value(lines[y])
            # print("cell_type, cell_value ==== ",cell_type, cell_value)
            if cell_type == 'date':
                sheet.write_datetime(y + y_offset, 0, cell_value, date_default_col1_style)
            else:
                sheet.write(y + y_offset, 0, cell_value, col1_style)

            #write all the remaining cells
            for x in range(1, len(lines[y]['columns']) + 1):
                cell_type, cell_value = self._get_cell_type_value(lines[y]['columns'][x - 1])
                if cell_type == 'date':
                    sheet.write_datetime(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, date_default_style)
                else:
                    if self._name in ['horoscope.report', 'horoscope.report.vendors']:
                        chk_data = x + lines[y].get('colspan', 1) - 1
                        if chk_data != 5 and chk_data != 6 and chk_data != 7 and chk_data != 4 and chk_data != 3:
                            if chk_data == 8 :
                                sheet.write(y + y_offset, 2, cell_value, style)
                            elif chk_data == 9 :
                                sheet.write(y + y_offset, 3, cell_value, style)
                            else:
                                sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)
                    elif self._name == 'account.check.receivable.report':
                        if y+y_offset ==1 and y == 0 and cell_value:
                            cell_value = ''
                            sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)
                        else:
                            sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)
                    else:
                        sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)


        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file

    def get_html(self, options, line_id=None, additional_context=None):
        '''
        return the html value of report, or html value of unfolded line
        * if line_id is set, the template used will be the line_template
        otherwise it uses the main_template. Reason is for efficiency, when unfolding a line in the report
        we don't want to reload all lines, just get the one we unfolded.
        '''
        # Prevent inconsistency between options and context.
        self = self.with_context(self._set_context(options))

        templates = self._get_templates()
        report_manager = self._get_report_manager(options)

        render_values = {
            'report': {
                'name': self._get_report_name(),
                'summary': report_manager.summary,
                'company_name': self.env.company.name,
            },
            'options': options,
            'context': self.env.context,
            'model': self,
        }
        if additional_context:
            render_values.update(additional_context)

        # Create lines/headers.
        if line_id:
            headers = options['headers']
            lines = self._get_lines(options, line_id=line_id)
            template = templates['line_template']
        else:
            headers, lines = self._get_table(options)
            options['headers'] = headers
            template = templates['main_template']
        if options.get('hierarchy'):
            lines = self._create_hierarchy(lines, options)
        if options.get('selected_column'):
            lines = self._sort_lines(lines, options)
        if self._name in ['horoscope.report', 'horoscope.report.vendors']:
            # headers['added_new_colspan'] = '5'
            new_header = []
            # print("headers ****** ",headers)
            for nh in headers[0]:
                # print("nh === ",nh)
                new_dct = {}
                if nh.get('name') in ['1 - 30', '31 - 60', '61 - 90', '91 - 120', 'Older', 'As of: 08/25/2022']:
                    # print("nh === ",nh)
                    nh['new_merger_data']=True
                    new_dct.update(nh)
                    new_header.append(new_dct)
                else:
                    if nh.get('name') == 'Total':
                        nh['new_merger_total_data']=True
                        new_dct.update(nh)
                        new_header.append(new_dct)
                    else:
                        new_dct.update(nh)
                        new_header.append(new_dct)
            headers = [new_header]
        render_values['lines'] = {'columns_header': headers, 'lines': lines}

        # Manage footnotes.
        footnotes_to_render = []
        if self.env.context.get('print_mode', False):
            # we are in print mode, so compute footnote number and include them in lines values, otherwise, let the js compute the number correctly as
            # we don't know all the visible lines.
            footnotes = dict([(str(f.line), f) for f in report_manager.footnotes_ids])
            number = 0
            for line in lines:
                f = footnotes.get(str(line.get('id')))
                if f:
                    number += 1
                    line['footnote'] = str(number)
                    footnotes_to_render.append({'id': f.id, 'number': number, 'text': f.text})

        # Render.
        html = self.env.ref(template)._render(render_values)
        if self.env.context.get('print_mode', False):
            for k,v in self._replace_class().items():
                html = html.replace(k, v)
            # append footnote as well
            html = html.replace(b'<div class="js_account_report_footnotes"></div>', self.get_html_footnotes(footnotes_to_render))
        return html


class AccountingReport(models.AbstractModel):
    _inherit = 'account.accounting.report'

    # COLUMN/CELL FORMATTING ###################################################
    # ##########################################################################
    def _field_column(self, field_name, sortable=False, name=None):
        """Build a column based on a field.

        The type of the field determines how it is displayed.
        The column's title is the name of the field.
        :param field_name: The name of the fields.Field to use
        :param sortable: Allow the user to sort data based on this column
        :param name: Use a specific name for display.
        """
        classes = ['text-nowrap']
        def getter(v): return v.get(field_name, '')
        if self._fields[field_name].type in ['monetary', 'float']:
            classes += ['number']
            def formatter(v): return self.format_value(v)
        elif self._fields[field_name].type in ['char']:
            classes += ['text-center']
            def formatter(v): return v
        elif self._fields[field_name].type in ['date']:
            classes += ['date']
            def formatter(v): return format_date(self.env, v)
        IrModelFields = self.env['ir.model.fields']
        # print("self._context == ",self._context)
        if 'hide_data' in self._context:
            classes += ['d-none', 'd-print-block']
        return self._custom_column(name=name or IrModelFields._get(self._name, field_name).field_description,
                                   getter=getter,
                                   formatter=formatter,
                                   classes=classes,
                                   sortable=sortable)


class ResPartnerInh(models.Model):
    _inherit = 'res.partner'

    employee = fields.Many2one('hr.employee', string='Employee', tracking = True)

    def action_update_employee(self):
        search_user = self.user_id.search([('partner_id', '=', self.id)], limit=1)
        if search_user and search_user.employee_ids:
            self.employee = search_user.employee_ids.id

class Task(models.Model):
    _inherit = "project.task"

    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super(Task, self).create(vals_list)
    #     for vals in vals_list:
    #         if 'partner_id' in vals:
    #             if res.partner_id.company_id.apply_credit_limit and res.partner_id.credit_limit_on_hold:
    #                 raise ValidationError(_('Credit Limit is on hold for the selected customer'))
    #     return res

    # def write(self, vals):
    #     res = super(Task, self).write(vals)
    #     if 'partner_id' in vals:
    #         if self.partner_id.company_id.apply_credit_limit and self.partner_id.credit_limit_on_hold:
    #             raise ValidationError(_('Credit Limit is on hold for the selected customer'))
    #     return res

    def action_fsm_create_quotation(self):
        view_form_id = self.env.ref('sale.view_order_form').id
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations")
        action.update({
            'views': [(view_form_id, 'form')],
            'view_mode': 'form',
            'name': self.name,
            'context': {
                'fsm_mode': True,
                'form_view_initial_mode': 'edit',
                'default_partner_id': self.partner_id.id,
                'default_task_id': self.id,
                'default_x_studio_vendedor_oficial_1':self.technician.employee.id,
                'default_company_id': self.company_id.id,             
            },
        })
        return action

    def _fsm_create_sale_order(self):
        """ Create the SO from the task, with the 'service product' sales line and link all timesheet to that line it """
        if not self.partner_id:
            raise UserError(_('A customer should be set on the task to generate a worksheet.'))

        SaleOrder = self.env['sale.order']
        if self.user_has_groups('project.group_project_user'):
            SaleOrder = SaleOrder.sudo()

        domain = ['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)]
        team = self.env['crm.team'].sudo()._get_default_team_id(domain=domain)
        sale_order = SaleOrder.create({
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'task_id': self.id,
            'analytic_account_id': self.project_id.analytic_account_id.id,
            'team_id': team.id if team else False,
            'x_studio_vendedor_oficial_1':self.technician.employee.id,
        })
        sale_order.onchange_partner_id()

        # write after creation since onchange_partner_id sets the current user
        sale_order.write({'user_id': self.user_id.id})
        sale_order.onchange_user_id()

        self.sale_order_id = sale_order

    def _fsm_ensure_sale_order(self):
        """ get the SO of the task. If no one, create it and return it """
        sale_order = self.sale_order_id
        if not sale_order:
            sale_order = self._fsm_create_sale_order()
        if self.project_id.allow_timesheets and not self.sale_line_id:
            self._fsm_create_sale_order_line()
        return sale_order

    def _fsm_create_sale_order_line(self):
        sale_order_line = self.env['sale.order.line'].sudo().create({
            'order_id': self.sale_order_id.id,
            'product_id': self.project_id.timesheet_product_id.id,
            'project_id': self.project_id.id,
            'task_id': self.id,
            'product_uom_qty': self.total_hours_spent,
            'product_uom': self.project_id.timesheet_product_id.uom_id.id,
        })
        self.write({
            'sale_line_id': sale_order_line.id,
        })

        # assign SOL to timesheets
        self.env['account.analytic.line'].sudo().search([
            ('task_id', '=', self.id),
            ('so_line', '=', False),
            ('project_id', '!=', False)
        ]).write({
            'so_line': sale_order_line.id
        })

class HrEmployeePrivate(models.Model):
    _inherit = "hr.employee"

    # techpartner_id = fields.Many2one('res.partner',string="Tech Partner", tracking = True)

    @api.model
    def create(self, vals):
        res = super(HrEmployeePrivate, self).create(vals)
        if 'address_home_id' in vals and vals.get('address_home_id'):
            res.address_home_id.employee = res.id
        return res

    def write(self, vals):
        address_home_id = False
        if 'address_home_id' in vals:
            address_home_id = self.address_home_id
        res = super(HrEmployeePrivate, self).write(vals)
        if 'address_home_id' in vals and vals.get('address_home_id'):
            self.address_home_id.employee = self.id
            if address_home_id:
                address_home_id.employee = False
        if 'address_home_id' in vals and not vals.get('address_home_id'):
            if address_home_id:
                address_home_id.employee = False
        return res


class ResCompany(models.Model):
    _inherit = "res.company"

    branch_ln = fields.Text(string="Branch line")        
