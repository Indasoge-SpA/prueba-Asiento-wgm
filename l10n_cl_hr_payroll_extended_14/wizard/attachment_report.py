from odoo import api, fields, models, tools, _


class AttachmentReport(models.TransientModel):
    _name = 'attachment.report'
    _description = 'Attachment Reports'

    attachment = fields.Binary('Attachment')
    filename = fields.Char('File Name')
