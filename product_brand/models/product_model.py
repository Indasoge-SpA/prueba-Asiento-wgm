 #-*- coding: utf-8 -*-

# Copyright 2009 NetAndCo (<http://www.netandco.net>).
# Copyright 2011 Akretion Benoît Guillot <benoit.guillot@akretion.com>
# Copyright 2014 prisnet.ch Seraphine Lantible <s.lantible@gmail.com>
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Daniel Campos <danielcampos@avanzosc.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ProductModel(models.Model):
    _name = "product.model"
    _description = "Product Model"
    _order = "name"

    name = fields.Char("Model Name", required=True)
    description = fields.Text(translate=True)
    
    logo = fields.Binary("Logo File")

    product_mybrand_id = fields.Many2one("product.brand",string="Brand")

    product_ids = fields.One2many(
        "product.template", "product_model_id", string="Model Products"
    )
    products_count = fields.Integer(
        string="Number of products", compute="_compute_products_count"
    )

    @api.depends("product_ids")
    def _compute_products_count(self):
        product_model = self.env["product.template"]
        groups = product_model.read_group(
            [("product_model_id", "in", self.ids)],
            ["product_model_id"],
            ["product_model_id"],
            lazy=False,
        )
        data = {group["product_model_id"][0]: group["__count"] for group in groups}
        for model in self:
            model.products_count = data.get(model.id, 0)




