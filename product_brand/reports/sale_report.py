 #-*- coding: utf-8 -*-

# Copyright 2018 Tecnativa - David Vidal
# Copyright 2020 Tecnativa - João Marques
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    product_brand_id = fields.Many2one(comodel_name="product.brand", string="Brand")
    product_model_id = fields.Many2one(comodel_name="product.model", string="Model")

    def _query(self, with_clause="", fields=None, groupby="", from_clause=""):
        fields = fields or {}
        fields["product_brand_id"] = ", t.product_brand_id as product_brand_id"
        fields["product_model_id"] = ", t.product_model_id as product_model_id"
        groupby += ", t.product_brand_id, t.product_model_id"
        return super()._query(with_clause, fields, groupby, from_clause)
