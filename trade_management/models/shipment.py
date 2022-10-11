#-*- coding: utf-8 -*-

from odoo import _,models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
import sys


class ShipmentOrigin(models.Model):
    _name = 'trade_management.shipment.origin'
    _description = 'Shipment Origins'

    name=fields.Char(string='Shipment Origin',required=True)
    shipment_ids = fields.One2many(comodel_name='trade_management.shipment',
                                inverse_name='shipment_origin_id',
                                string='Shipments')
    active = fields.Boolean(string='Active', required=True, default=True)
    description = fields.Text(string='Shipment Origin Description')

class ShipmentDestinationPort(models.Model):
    _name = 'trade_management.port.destination'
    _description = 'Shipment Destination Port'

    name=fields.Char(string='Destination Port',required=True)
    shipment_ids = fields.One2many(comodel_name='trade_management.shipment',
                                inverse_name='shipment_port_destination_id',
                                string='Shipments')
    active = fields.Boolean(string='Active', required=True, default=True)
    description = fields.Text(string='Shipment Destination Port Description')

class Container(models.Model):
    _name = 'trade_management.container'
    _description = 'Containers for Shipments'

    name=fields.Char(string='Container Name', required=True)
    active = fields.Boolean(string='Active',required=True, default=True)
    description = fields.Text(string='Container Details')
    shipment_id = fields.Many2one(comodel_name='trade_management.shipment',
                                ondelete='restrict',
                                string='Shipment')
    purchase_orders_ids = fields.One2many(comodel_name='purchase.order',
                                inverse_name='shipment_id',
                                string='Shipment Purchase Orders')
    purchase_orders_count = fields.Integer(string='PO Quantity', compute='_compute_purchase_orders_count')
    company_ownership = fields.Boolean(string='Container belongs to company',required=True, default=False)

    @api.depends('purchase_orders_ids')
    def _compute_purchase_orders_count(self):
        po_container = self.env['purchase.order']
        groups = po_container.read_group(
            [('container_id','in',self.ids)],
            ['container_id'],
            ['container_id'],
            lazy=False
        )
        data = {group['container_id'][0]: group['__count'] for group in groups}
        for container in self:
            container.purchase_orders_count = data.get(container.id, 0)

class Shipment(models.Model):
    _name = 'trade_management.shipment'
    _description = 'Shipment information and tracking'
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = "shipment_date desc"

    name = fields.Integer(string='Identifier', required=True)
    description = fields.Text(string='Shipment Information and Tracking')
    state = fields.Selection(string='State', 
                                selection=[('created','Created'),
                                    ('shipped','Shipped in Origin'),
                                    ('arrived','Arrived'),
                                    ('done','Completed')],
                                copy=False, default='created',
                                required=True,tracking=True,
                                index=True)
    transport_type = fields.Selection(string='Type',
                                selection=[('air','Air'),
                                    ('maritime','Maritime'),
                                    ('land','Land')],
                                copy=False, default='air',required=True)
    shipment_date = fields.Date(string='Date',default=datetime.now(),tracking=True)
    shipment_year = fields.Integer(string='Year')
    shipment_origin_id = fields.Many2one(comodel_name='trade_management.shipment.origin',
                                ondelete='restrict',
                                string='Origin', tracking=True)
    shipment_category_ids = fields.Many2many(comodel_name='product.category',
                                relation='categories_shipments_rel',
                                string='Category', 
                                domain = "[('parent_id','=',False)]", tracking=True)
    purchase_orders_ids = fields.One2many(comodel_name='purchase.order',
                                inverse_name='shipment_id',
                                string='Shipment Purchase Orders')
    purchase_orders_count = fields.Integer(string='PO Quantity',compute='_compute_purchase_orders_count')
    purchase_orders_confirmed = fields.Integer(string='PO Confirmed', compute='_compute_purchase_orders_completed')
    containers_ids = fields.One2many(comodel_name='trade_management.container',
                                inverse_name='shipment_id',
                                string='Shipment Containers')
    containers_count = fields.Integer(string='Containers Quantity', compute='_compute_containers_count')
    shipment_date_departure = fields.Date(string='Departure Date', tracking=True)
    shipment_port_destination_id = fields.Many2one(comodel_name='trade_management.port.destination',
                                ondelete='restrict',
                                string='Destination Port', tracking=True)
    shipment_date_arrival = fields.Date(string='Arrival Date', tracking=True)
    total_weight = fields.Float(string='Total Weight', tracking=True)
    containers_ids = fields.One2many(comodel_name='trade_management.container',
                                inverse_name='shipment_id',
                                string = 'Containers')
    bill_id = fields.Char(string='Bill number', tracking=True)

    @api.depends('purchase_orders_ids')
    def _compute_purchase_orders_count(self):
        po_shipment = self.env['purchase.order']
        groups = po_shipment.read_group(
                [('shipment_id','in',self.ids)],
                ['shipment_id'],
                ['shipment_id'],
                lazy=False
        )
        data = {group['shipment_id'][0]: group['__count'] for group in groups}
        for shipment in self:
            shipment.purchase_orders_count = data.get(shipment.id,0)

    @api.depends('purchase_orders_ids')
    def _compute_purchase_orders_completed(self):
        po_shipment = self.env['purchase.order']
        groups = po_shipment.read_group(
                [('shipment_id','in',self.ids),('state','=','purchase')],
                ['shipment_id'],
                ['shipment_id'],
                lazy=False
        )
        data = {group['shipment_id'][0]: group['__count'] for group in groups}
        for shipment in self:
            shipment.purchase_orders_confirmed = data.get(shipment.id,0)

    @api.depends('containers_ids')
    def _compute_containers_count(self):
        po_shipment = self.env['trade_management.container']
        groups = po_shipment.read_group(
                [('shipment_id','in',self.ids)],
                ['shipment_id'],
                ['shipment_id'],
                lazy=False
        )
        data = {group['shipment_id'][0]: group['__count'] for group in groups}
        for shipment in self:
            shipment.containers_count = data.get(shipment.id,0)
    
    @api.onchange('shipment_date')
    def _onchange_shipment_date(self):
        for record in self:
            self.shipment_year = self.shipment_date.year
    
    @api.constrains('shipment_date_departure','shipment_date_arrival')
    def _check_arrival_after_departure(self):
        for record in self:
            if record.shipment_date_departure:
                if record.shipment_date_arrival:
                    if record.shipment_date_arrival < record.shipment_date_departure:
                        raise ValidationError(_("Shipment date arrival %s can't precede departure date %s") 
                                % fields.Date.to_string(record.shipment_date_arrival) 
                                % fields.Date.to_string(record.shipment_date_departure))

    @api.model
    def _is_allowed_transition(self, old_state, new_state):
        allowed = [('created','shipped'),
                ('shipped','created'),
                ('shipped','arrived'),
                ('arrived','shipped'),
                ('arrived','done')]
        return (old_state, new_state)  in allowed

    def _check_po_confirmed(self, new_state):
        po_count_ok = self.purchase_orders_count > 0
        po_confirmed_ok = po_count_ok and (self.purchase_orders_confirmed == self.purchase_orders_count)
        if not po_confirmed_ok:
            raise UserError(_("A Shipment can't change to state %s if there is not at least a confirmed Purchase Order")
                        % new_state)
        return po_confirmed_ok

    def _check_dep_date(self, new_state):
        shpmt_dep_date_ok = not (self.shipment_date_departure == False)
        if not shpmt_dep_date_ok:
            raise UserError(_("A Shipment can't change to state %s without a departure date, please enter the Departure Date")
                        % new_state)
        return shpmt_dep_date_ok
    
    def _check_shpmt_origin(self, new_state):
        shpmt_origin_ok = not (self.shipment_origin_id.id == False)
        if not shpmt_origin_ok:
            raise UserError(_("A Shipment can't change to state %s without an origin port, please enter the Origin Port")
                        % new_state)
        return shpmt_origin_ok

    def _check_arr_date(self, new_state):
        shpmt_arr_date_ok = not (self.shipment_date_arrival == False)
        if not shpmt_arr_date_ok:
            raise UserError(_("A Shipment can't change to state %s without an arrival date, please enter the Arrival Date")
                        % new_state)
        return shpmt_arr_date_ok

    def _check_shpmt_destination(self,new_state):
        shpmt_destination_ok = not (self.shipment_port_destination_id.id == False)
        if not shpmt_destination_ok:
            raise UserError(_("A Shipment can't change to state %s without an destination port, please enter the Destination Port")
                        % new_state)
        return shpmt_destination_ok

    def _check_shpmt_bill(self,new_state):
        shpmt_bill_ok = not (self.bill_id == False)
        if not shpmt_bill_ok:
            raise UserError(_("A Shipment can't change to state %s without a vendors bill, please enter the Bill Number")
                        % new_state)
        return shpmt_bill_ok

    def _check_shpmt_weight(self,new_state):
        shpmt_weight_ok = not (self.total_weight == False)
        if not shpmt_weight_ok:
            raise UserError(_("A Shipment can't change to state %s without the shipment weight, please enter the Total Weight")
                        % new_state)
        return shpmt_weight_ok

    def change_state(self, new_state):
        for shippment in self:
            if sys.__stdin__.isatty():
                import pdb; pdb.set_trace()
            if shippment._is_allowed_transition(shippment.state, new_state):
                if shippment.state == 'created':
                    shippment._check_po_confirmed(new_state)
                    shippment._check_dep_date(new_state)
                    shippment._check_shpmt_origin(new_state)
                    shippment.state = new_state
                elif shippment.state == 'shipped':
                    if new_state == 'arrived':
                        shippment._check_po_confirmed(new_state)
                        shippment._check_dep_date(new_state)
                        shippment._check_shpmt_origin(new_state)
                        shippment._check_arr_date(new_state)
                        shippment._check_shpmt_destination(new_state)
                        shippment._check_shpmt_bill(new_state)
                        shippment.state = new_state
                    elif new_state == 'created':
                        shippment.state = new_state
                elif shippment.state == 'arrived':
                    if new_state == 'done':
                        shippment._check_po_confirmed(new_state)
                        shippment._check_dep_date(new_state)
                        shippment._check_shpmt_origin(new_state)
                        shippment._check_arr_date(new_state)
                        shippment._check_shpmt_destination(new_state)
                        shippment._check_shpmt_bill(new_state)
                        shippment._check_shpmt_weight(new_state)
                        shippment.state = new_state
                    elif new_state == 'shipped':
                        shippment.state = new_state
                elif shippment.state == 'done':
                    if new_state == 'arrived':
                        shippment.state = new_state                    
            else:
                raise UserError(_("A Shipment state change from %s to % is not allowed")
                        % new_state % shippment.state)
                continue
    
    def make_created(self):
        self.change_state('created')
    
    def make_shipped(self):
        self.change_state('shipped')

    def make_arrived(self):
        self.change_state('arrived')

    def make_done(self):
        self.change_state('done')