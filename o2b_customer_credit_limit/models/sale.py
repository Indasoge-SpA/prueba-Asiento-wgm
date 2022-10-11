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


class sale_order(models.Model):
    _inherit= 'sale.order'
    
    exceeded_amount = fields.Float('Exceeded Amount')
        
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('credit_limit', 'Credit limit'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    credit_limit_approved = fields.Boolean(string="Credit Limit Approved", copy=False)

    # @api.onchange('partner_id')
    # def onchange_partner_id(self):
    #     res= super(sale_order,self).onchange_partner_id()
    #     if self.partner_id:
    #         if self.partner_id.credit_limit_on_hold:
    #             msg= "Customer '" + self.partner_id.name + "' is on credit limit hold."
    #             return { 'warning': {'title': 'Credit Limit On Hold', 'message':msg } }

    def action_credit_limit_approve(self):
        self.credit_limit_approved = True
        self._message_log(body=_("Credit Limit Approved."))

    def action_sale_ok(self):
        if self.partner_id.credit_limit_on_hold and self.partner_id.apply_credit_limit:
            domain = [
                ('order_id.partner_id', '=', self.partner_id.id),
                ('order_id.state', 'in', ['sale', 'credit_limit'])]
            order_lines = self.env['sale.order.line'].search(domain)
            
            order = []
            to_invoice_amount = 0.0
            for line in order_lines:
                not_invoiced = line.product_uom_qty - line.qty_invoiced
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_id.compute_all(
                    price, line.order_id.currency_id,
                    not_invoiced,
                    product=line.product_id, partner=line.order_id.partner_id)
                if line.order_id.id not in order:
                    if line.order_id.invoice_ids:
                        for inv in line.order_id.invoice_ids:
                            if inv.state == 'draft':
                                order.append(line.order_id.id)
                                break
                    else:
                        order.append(line.order_id.id)
                    
                to_invoice_amount += taxes['total_included']
            
            domain = [
                ('move_id.partner_id', '=', self.partner_id.id),
                ('move_id.payment_state', '!=', 'paid'),
                ('sale_line_ids', '!=', False)]
            draft_invoice_lines = self.env['account.move.line'].search(domain)
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
                exceeded_amount = (to_invoice_amount + draft_invoice_lines_amount + self.partner_id.credit + self.amount_total) - self.partner_id.credit_limit
                vals_wiz={
                    'partner_id':self.partner_id.id,
                    'sale_orders': total_amount if total_amount else self.partner_id.total_due,
                    'invoices':str(len(invoice))+' Draft Invoice worth : '+ str(draft_invoice_lines_amount),
                    'current_sale':self.amount_total or 0.0,
                    'exceeded_amount':exceeded_amount,
                    'credit':self.partner_id.credit,
                    'credit_limit_on_hold':self.partner_id.credit_limit_on_hold,
                    }
                wiz_id=self.env['customer.limit.wizard'].create(vals_wiz)
                action = imd.sudo().xmlid_to_object('o2b_customer_credit_limit.action_customer_limit_wizard')
                form_view_id=imd.xmlid_to_res_id('o2b_customer_credit_limit.view_customer_limit_wizard_form')
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
            else:
                self.action_confirm()
        else:
            self.action_confirm()
        return True
        
        
    
    def _make_url(self,model='sale.order'):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='http://localhost:8069')
        if base_url:
            base_url += '/web?db=%s&login=%s&key=%s#id=%s&model=%s' % (self._cr.dbname, '', '', self.id, model)
        return base_url


    def send_mail_approve_credit_limit(self):
        template = self.env.ref('o2b_customer_credit_limit.credit_limit_template_mail', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        url = self._make_url('sale.order')
        ctx = dict(
            default_model='sale.order',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            url = url,
            custom_layout="o2b_customer_credit_limit.mail_template_data_notification_email_credit_limit"
        )
        self.env['mail.template'].browse(template.id).with_context(ctx).send_mail(self.id,force_send=True)

class AccountMoveInh(models.Model):
    _inherit= 'account.move'

    # overdue_date = fields.Date(string='Overdue Date')
    credit_limit_on_hold  = fields.Boolean(string='Credit limit on hold', related='partner_id.credit_limit_on_hold')

    def update_invoice_date_due(self):
        self.invoice_date_due = datetime.now().date() - timedelta(days=31)