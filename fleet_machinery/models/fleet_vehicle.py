# -*- coding: utf-8 -*-

from odoo import models, fields, api

class FleetVehicle(models.Model):
    _name = 'fleet.vehicle'
    _inherit = 'fleet.vehicle'

    odometer_unit = fields.Selection(selection_add=[('hours', 'hrs')], ondelete={'hours':'set default'})

