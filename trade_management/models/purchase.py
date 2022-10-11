# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit='purchase.order'

    transport_type = fields.Selection(string='Transport Type',
        selection=[('air','Air'),
                    ('maritime','Maritime'),
                    ('land','Land')], 
                    copy=False, default='air')

    shipment_id = fields.Many2one(comodel_name="trade_management.shipment",
                                ondelete="restrict",
                                string="Shipment")
    container_id = fields.Many2one(comodel_name='trade_management.container',
                                ondelete='restrict',
                                string='Container',
                                domain="[('shipment_id','=',shipment_id)]")
    notes= fields.Text(string='Notes')
    
    @api.onchange('shipment_id')
    def _onchange_shipment(self):
        for record in self:
            if record.shipment_id.transport_type == 'air':
                record.transport_type = 'air'
            elif record.shipment_id.transport_type == 'maritime':
                record.transport_type = 'maritime'
            else:
                record.transport_type = 'land'


