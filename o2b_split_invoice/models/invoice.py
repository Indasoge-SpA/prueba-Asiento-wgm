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
from odoo.exceptions import UserError
from json import dumps
import json

class AccountMove(models.Model):
    _inherit = "account.move"

   
    third_party_amt = fields.Float(string="Third Party Amount", readonly=True)
    third_party = fields.Many2one('res.partner', string="Third Party")
    mv_bnk_amt = fields.Float(string="Bank Amount")

    def write(self,vals):
        res = super(AccountMove, self).write(vals)
        if self.third_party:
            if self.mv_bnk_amt < 0.00:
                raise UserError(_('Amount entered cannot be negative.'))
            if self.mv_bnk_amt > self.amount_total:
                raise UserError(_('Amount entered cannot be more than invoice amount.'))

        if 'mv_bnk_amt' in vals and vals.get('mv_bnk_amt') or vals.get('mv_bnk_amt') == 0.0:
            a = self.amount_total
            b = self.mv_bnk_amt
            third_party_amt = a - b
            self.third_party_amt = third_party_amt                    
        return res


    def _compute_payments_widget_to_reconcile_info(self):
        for move in self:
            move.invoice_outstanding_credits_debits_widget = json.dumps(False)
            move.invoice_has_outstanding = False

            if move.state != 'posted' \
                    or move.payment_state not in ('not_paid', 'partial') \
                    or not move.is_invoice(include_receipts=True):
                continue

            pay_term_lines = move.line_ids\
                .filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            if move.third_party:
                domain = [
                    ('account_id', 'in', pay_term_lines.account_id.ids),
                    ('parent_state', '=', 'posted'),
                    ('reconciled', '=', False),
                    '|',
                    ('partner_id', '=', move.commercial_partner_id.id),
                    ('partner_id', '=', move.third_party.id),
                    '|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
                ]
            else:
                domain = [
                    ('account_id', 'in', pay_term_lines.account_id.ids),
                    ('parent_state', '=', 'posted'),
                    ('partner_id', '=', move.commercial_partner_id.id),
                    ('reconciled', '=', False),
                    '|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
                ]

            payments_widget_vals = {'outstanding': True, 'content': [], 'move_id': move.id}
            if move.is_inbound():
                domain.append(('balance', '<', 0.0))
                payments_widget_vals['title'] = _('Outstanding credits')
            else:
                domain.append(('balance', '>', 0.0))
                payments_widget_vals['title'] = _('Outstanding debits')

            for line in self.env['account.move.line'].search(domain):

                if line.currency_id == move.currency_id:
                    # Same foreign currency.
                    amount = abs(line.amount_residual_currency)
                else:
                    # Different foreign currencies.
                    amount = move.company_currency_id._convert(
                        abs(line.amount_residual),
                        move.currency_id,
                        move.company_id,
                        line.date,
                    )

                if move.currency_id.is_zero(amount):
                    continue

                payments_widget_vals['content'].append({
                    'journal_name': line.ref or line.move_id.name,
                    'amount': amount,
                    'currency': move.currency_id.symbol,
                    'id': line.id,
                    'move_id': line.move_id.id,
                    'position': move.currency_id.position,
                    'digits': [69, move.currency_id.decimal_places],
                    'payment_date': fields.Date.to_string(line.date),
                })

            if not payments_widget_vals['content']:
                continue

            move.invoice_outstanding_credits_debits_widget = json.dumps(payments_widget_vals)
            move.invoice_has_outstanding = True

    
class SaleOrder(models.Model):
    _inherit = "sale.order"

    third_party = fields.Many2one('res.partner', string="Third Party")    