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

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    advance_payment_method = fields.Selection(selection_add=[('bank_amount', 'Bank Amount')], ondelete={'bank_amount': 'set default'})
    bk_amt = fields.Float(string="Bank Amount")

    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))

        if self.advance_payment_method == 'delivered' or self.advance_payment_method == 'bank_amount':
            invoice = sale_orders._create_invoices(final=self.deduct_down_payments)
            if invoice:
                if self.advance_payment_method == 'bank_amount':
                    if sale_orders and not sale_orders.third_party:
                        raise UserError(_('Bank Amount is only applicable for third_party.'))
    
                    if self.bk_amt < 0.00:
                        raise UserError(_('Amount entered cannot be negative.'))
                    if self.bk_amt > invoice.amount_total:
                        raise UserError(_('Amount entered cannot be more than invoice amount.'))
    
                    a = invoice.amount_total
                    b = self.bk_amt
                    third_party_amt = a - b
                    invoice.write({
                        'third_party_amt': third_party_amt,
                        'third_party': sale_orders.third_party,
                        'mv_bnk_amt': self.bk_amt
                        })
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id', self.product_id.id)

            sale_line_obj = self.env['sale.order.line']
            for order in sale_orders:
                amount, name = self._get_advance_details(order)

                if self.product_id.invoice_policy != 'order':
                    raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
                tax_ids = order.fiscal_position_id.map_tax(taxes, self.product_id, order.partner_shipping_id).ids
                analytic_tag_ids = []
                for line in order.order_line:
                    analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

                so_line_values = self._prepare_so_line(order, analytic_tag_ids, tax_ids, amount)
                so_line = sale_line_obj.create(so_line_values)
                self._create_invoice(order, so_line, amount)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    
    third_party_check = fields.Boolean(string="Third Party")
    third_party_wiz = fields.Many2one('res.partner', string="Third Party", readonly=True)


    @api.model
    def default_get(self, fields_list):
        # OVERRIDE
        res = super(AccountPaymentRegister, self).default_get(fields_list)
        if self._context.get('active_model') == 'account.move':
            
            account_move = self.env['account.move'].browse(self._context.get('active_ids', []))
            if account_move and account_move.third_party:
                res['third_party_wiz'] = account_move.third_party.id
        return res

    def _create_payment_vals_from_wizard(self):
        payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        if payment_vals and self.third_party_check and self.third_party_wiz:
            payment_vals.update({
                'partner_id': self.third_party_wiz.id
                })
        return payment_vals       
       
           
            
        
