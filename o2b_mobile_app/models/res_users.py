# Copyright 2018 Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api,_
from odoo import http
from odoo.exceptions import UserError, ValidationError, RedirectWarning
import requests
import datetime
from datetime import date 
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
from odoo.addons.http_routing.models.ir_http import slug
import logging
import string 
import random 
import werkzeug.urls
from ast import literal_eval
from odoo import release, SUPERUSER_ID
from odoo.models import AbstractModel
from odoo.tools.translate import _
from odoo.tools import config, misc, ustr
import qrcode
import base64
from io import BytesIO
import random
from random import randint
from passlib.context import CryptContext

crypt_context = CryptContext(schemes=['pbkdf2_sha512', 'plaintext'],
                             deprecated=['plaintext'])

_logger = logging.getLogger(__name__)

class ProductDetails(models.Model):
    _name = 'product.detail.line'
    _description = 'Product Line'

    task_id = fields.Many2one('project.task')
    product_name = fields.Many2one('product.product', string='Product')
    product_quant = fields.Integer(string='Product Quantity',default=1)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    # qrcode_img = fields.Binary("QRCode", attachment=True, store=True, copy=False)
    barcode_gen = fields.Char(string='Barcode')
    technician = fields.Many2one('res.partner', string='Technician')
    work_type = fields.Selection([
        ('internalrepair', 'Internal Repair'),
        ('externalrepair', 'External Repair'),
        ])
    name = fields.Char(string="Task Number", readonly=True, required=True, copy=False, default='New')
    product_detail_line = fields.One2many('product.detail.line','task_id',string='Product Line')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('project.task') or 'New'
            # print("taskno====================================>>>",vals['name'])
        result = super(ProjectTask, self).create(vals)
        result.barcode_gen = "yes-" + str(result.id)
        return result

    # def action_generate_qrcode(self):
    #     base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     # self._compute_website_url()
    #     # qrcode_url = base_url+self.website_url
    #     qrcode_url = base_url +'-'+str(self.id)
    #     qr = qrcode.QRCode(
    #         version=1,
    #         error_correction=qrcode.constants.ERROR_CORRECT_L,
    #         box_size=20,
    #         border=4,
    #     )
    #     qr.add_data(qrcode_url)
    #     qr.make(fit=True)
    #     img = qr.make_image()
    #     temp = BytesIO()
    #     img.save(temp, format="PNG")
    #     qr_image = base64.b64encode(temp.getvalue())
    #     self.qrcode_img = qr_image

    # @api.model
    # def create(self, vals):
    #     res = super(ProjectTask, self).create(vals)
    #     res.action_generate_qrcode()
    #     return res

class PartnerInherit(models.Model):
    _inherit = 'res.partner'
    is_technician = fields.Boolean(default=False, string='Is Technician')