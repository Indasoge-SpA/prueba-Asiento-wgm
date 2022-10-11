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

from odoo import api, fields, models, _


class customer_limit_wizard(models.TransientModel):
    _name = "customer.limit.wizard"
    _description = 'customer limit wizard'

    
    def set_credit_limit_state(self):
        order_id = self.env['sale.order'].browse(self._context.get('active_id'))
        order_id.state = 'credit_limit'
        order_id.exceeded_amount = self.exceeded_amount
        order_id.send_mail_approve_credit_limit()
        self.partner_id.credit_limit_on_hold = self.credit_limit_on_hold
        return True
    
    current_sale = fields.Float('Current Quotation')
    exceeded_amount = fields.Float('Exceeded Amount')
    credit = fields.Float('Total Receivable Open Invoice')
    partner_id = fields.Many2one('res.partner',string="Customer")
    credit_limit = fields.Float(related='partner_id.credit_limit',string="Credit Limit")
    sale_orders = fields.Char("Pending Invoice Amount")
    invoices = fields.Char("Draft Invoices")
    credit_limit_on_hold = fields.Boolean('Credit Limit on Hold')
    from_field_service = fields.Boolean('From Field Service')
