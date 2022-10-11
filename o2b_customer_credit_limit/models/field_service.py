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

import time
from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
from datetime import datetime, timedelta

# class ProjectTags(models.Model):
#     _inherit = 'project.tags'

#     credit_limit_process = fields.Selection([('credit_limit_exceeded', 'Credit Limit Exceeded'),
#         ('wating', 'Waiting'),
#         ('approved', 'Approved')], string="Credit Limit Tag")

class ProjectTask(models.Model):
    _inherit= 'project.task'

    credit_limit_on_hold  = fields.Boolean(string='Credit limit on hold', related='partner_id.credit_limit_on_hold')
    company_credit_limit_on_hold = fields.Boolean(string='Company limit on hold', related='company_id.apply_credit_limit')
    credit_limit_approved = fields.Boolean(string="Credit Limit Approved", copy=False)
    pending_for_approval = fields.Boolean(string="Pending For Approval", copy=False)
    is_closed = fields.Boolean(related='stage_id.is_closed')
    # tag_ids = fields.Many2many('project.tags', string='Tags', tracking=True)

    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super(ProjectTask, self).create(vals_list)
    #     credit_limit_process = res.tag_ids.search([('credit_limit_process', '=', 'credit_limit_exceeded')], limit=1)
    #     for vals in vals_list:
    #         if 'partner_id' in vals and vals.get('partner_id') and res.company_credit_limit_on_hold and res.credit_limit_on_hold and credit_limit_process:
    #             res.tag_ids = [(4, credit_limit_process.id)]
    #     return res

    # def write(self, vals):
    #     res = super(ProjectTask, self).write(vals)
    #     credit_limit_process = self.tag_ids.search([('credit_limit_process', '=', 'credit_limit_exceeded')], limit=1)
    #     credit_limit_waiting = self.tag_ids.search([('credit_limit_process', '=', 'wating')], limit=1)
    #     credit_limit_approved = self.tag_ids.search([('credit_limit_process', '=', 'approved')], limit=1)
    #     if 'partner_id' in vals:
    #         if self.company_credit_limit_on_hold and self.credit_limit_on_hold and credit_limit_process:
    #             self.tag_ids = [(4, credit_limit_process.id)]
    #     return res

    def action_credit_limit_approve(self):
        # credit_limit_waiting = self.tag_ids.search([('credit_limit_process', '=', 'wating')], limit=1)
        # credit_limit_approved = self.tag_ids.search([('credit_limit_process', '=', 'approved')], limit=1)
        # if self.tag_ids and credit_limit_waiting and credit_limit_waiting.id in self.tag_ids.ids:
        #     self.tag_ids = [(3, credit_limit_waiting.id)]
        # if credit_limit_approved:
        #     self.tag_ids = [(4, credit_limit_approved.id)]
        self.write({
            'credit_limit_approved': True,
            'pending_for_approval': False
            })
        self._message_log(body=_("Credit Limit Approved."))

    def action_submit_for_approval(self):
        self.pending_for_approval = True
        # credit_limit_process = self.tag_ids.search([('credit_limit_process', '=', 'credit_limit_exceeded')], limit=1)
        # credit_limit_waiting = self.tag_ids.search([('credit_limit_process', '=', 'wating')], limit=1)
        # if self.tag_ids and credit_limit_process and credit_limit_process.id in self.tag_ids.ids:
        #     self.tag_ids = [(3, credit_limit_process.id)]
        # if credit_limit_waiting:
        #     self.tag_ids = [(4, credit_limit_waiting.id)]
        if self.partner_id.credit_limit_on_hold and self.company_credit_limit_on_hold:
            domain = [
                ('move_id.partner_id', '=', self.partner_id.id),
                ('move_id.payment_state', '!=', 'paid'),
                ('sale_line_ids', '!=', False)]
            draft_invoice_lines = self.env['account.move.line'].search(domain)
            to_invoice_amount = 0.0
            for line in draft_invoice_lines:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_ids.compute_all(
                    price, line.move_id.currency_id,
                    line.quantity,
                    product=line.product_id, partner=line.move_id.partner_id)
                to_invoice_amount += taxes['total_included']

            # We sum from all the invoices lines that are in draft and not linked
            # to a sale order
            domain = [
                ('move_id.partner_id', '=', self.partner_id.id),
                ('move_id.state', '=', 'draft'),
                ('sale_line_ids', '=', False)]
            draft_invoice_lines = self.env['account.move.line'].search(domain)
            draft_invoice_lines_amount = 0.0
            invoice=[]
            for line in draft_invoice_lines:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_ids.compute_all(
                    price, line.move_id.currency_id,
                    line.quantity,
                    product=line.product_id, partner=line.move_id.partner_id)
                draft_invoice_lines_amount += taxes['total_included']
                if line.move_id.id not in invoice:
                    invoice.append(line.move_id.id)

            available_credit = self.partner_id.credit_limit - \
                self.partner_id.credit - \
                to_invoice_amount - draft_invoice_lines_amount
            overdue_days = self.env['ir.config_parameter'].sudo().get_param('account.overdue_days')
            if not overdue_days:
                overdue_days = 30    
            futuredate = datetime.now() + timedelta(days=int(overdue_days))
           
            find_inv_domain = [
                ('partner_id', '=', self.partner_id.id),
                ('payment_state', '!=', 'paid'),
                ('invoice_date_due', '<=', futuredate)]
            find_inv = self.env['account.move'].search(find_inv_domain)
            new_find_inv_domain = [
                ('partner_id', '=', self.partner_id.id),
                ('payment_state', '!=', 'paid')]
            new_find_inv = self.env['account.move'].search(new_find_inv_domain)
            find_inv = new_find_inv.filtered(lambda ls: ls.invoice_date_due and ls.invoice_date_due + timedelta(days=int(overdue_days)) < datetime.now().date())

            if find_inv:
                total_amount_mapped = find_inv.mapped('amount_residual')
                total_amount = sum(total_amount_mapped)
                imd = self.env['ir.model.data']
                exceeded_amount = (to_invoice_amount + draft_invoice_lines_amount + self.partner_id.credit ) - self.partner_id.credit_limit
                vals_wiz={
                    'partner_id':self.partner_id.id,
                    'sale_orders': total_amount if total_amount else self.partner_id.total_due,
                    'invoices':str(len(invoice))+' Draft Invoice worth : '+ str(draft_invoice_lines_amount),
                    # 'current_sale':self.amount_total or 0.0,
                    'exceeded_amount':exceeded_amount,
                    'credit':self.partner_id.credit,
                    'credit_limit_on_hold':self.partner_id.credit_limit_on_hold,
                    'from_field_service': True
                    }
                wiz_id=self.env['customer.limit.wizard'].create(vals_wiz)
                action = imd.sudo().xmlid_to_object('o2b_customer_credit_limit.action_customer_limit_wizard')
                form_view_id=imd.xmlid_to_res_id('o2b_customer_credit_limit.view_customer_limit_wizard_form')
                print("action.context --- ",action.context)
                # context = action.context.update({'from_field_service': True})
                return  {
                        'name': action.name,
                        'help': action.help,
                        'type': action.type,
                        'views': [(form_view_id, 'form')],
                        'view_id': form_view_id,
                        'target': action.target,
                        'context': action.context,
                        'res_model': action.res_model,
                        'res_id':wiz_id.id,
                    }