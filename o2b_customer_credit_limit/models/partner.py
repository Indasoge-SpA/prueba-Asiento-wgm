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

from odoo import api, models, fields, _
from datetime import datetime, timedelta

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    overdue_days = fields.Integer('Overdue Days', default=30, config_parameter='account.overdue_days')

class res_partner(models.Model):
    _inherit= 'res.partner'

    check_credit = fields.Boolean('Check Credit',default=True, copy=False)
    credit_limit_on_hold  = fields.Boolean('Credit limit on hold', copy=False)
    credit_limit = fields.Float('Credit Limit',default=0.00)
    apply_credit_limit = fields.Boolean(related='company_id.apply_credit_limit', string="Apply Credit Limit")

    
    def _compute_for_followup(self):
        """
        Compute the fields 'total_due', 'total_overdue','followup_level' and 'followup_status'
        """
        first_followup_level = self.env['account_followup.followup.line'].search([('company_id', '=', self.env.company.id)], order="delay asc", limit=1)
        followup_data = self._query_followup_level()
        today = fields.Date.context_today(self)
        overdue_days = self.env['ir.config_parameter'].sudo().get_param('account.overdue_days')
        for record in self:
            total_due = 0
            total_overdue = 0
            followup_status = "no_action_needed"
            credit_limit_on_hold = False
            futuredate = datetime.now() + timedelta(days=int(overdue_days))
            check_unpaid_inv = self.unpaid_invoices.search(
                [('partner_id', '=', record.id),
                ('payment_state', '!=', 'paid'),
                ('state', '=', 'posted'),
                ('invoice_date_due', '<=', futuredate)])
            if check_unpaid_inv:
                credit_limit_on_hold = True

            for aml in record.unreconciled_aml_ids:
                if aml.company_id == self.env.company:
                    amount = aml.amount_residual
                    total_due += amount
                    is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                    overdue_date = False
                    if aml.date_maturity:
                        overdue_date = aml.date_maturity + timedelta(days=int(overdue_days))
                    if aml.move_id and overdue_date and aml.date_maturity and record.company_id.apply_credit_limit and today > overdue_date:
                        credit_limit_on_hold = True
                    # else:
                    #     credit_limit_on_hold = False
                    if is_overdue and not aml.blocked:
                        total_overdue += amount
            record.total_due = total_due
            record.total_overdue = total_overdue
            record.credit_limit_on_hold = credit_limit_on_hold if record.company_id and record.company_id.apply_credit_limit else False
            if record.id in followup_data:
                record.followup_status = followup_data[record.id]['followup_status']
                record.followup_level = self.env['account_followup.followup.line'].browse(followup_data[record.id]['followup_level']) or first_followup_level
            else:
                record.followup_status = 'no_action_needed'
                record.followup_level = first_followup_level

class res_company(models.Model):
    _inherit= 'res.company'

    apply_credit_limit = fields.Boolean('Apply Credit Limit', copy=False)                