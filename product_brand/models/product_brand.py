 #-*- coding: utf-8 -*-

# Copyright 2009 NetAndCo (<http://www.netandco.net>).
# Copyright 2011 Akretion Benoît Guillot <benoit.guillot@akretion.com>
# Copyright 2014 prisnet.ch Seraphine Lantible <s.lantible@gmail.com>
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Daniel Campos <danielcampos@avanzosc.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
import logging
_logger=logging.getLogger(__name__)

class ProductBrand(models.Model):
    _name = "product.brand"
    _description = "Product Brand"
    _order = "name"

    name = fields.Char("Brand Name", required=True)
    description = fields.Text(translate=True)
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Select a partner for this brand if any.",
        ondelete="restrict",
    )
    logo = fields.Binary("Logo File")
    product_ids = fields.One2many(
        "product.template", "product_brand_id", string="Brand Products"
    )
    products_count = fields.Integer(
        string="Number of products", compute="_compute_products_count"
    )

    brand_model_ids = fields.One2many(
        "product.model", "product_mybrand_id", string="Brand Models"
    )
    models_count = fields.Integer(
        string="Number of Models", compute="_compute_models_count"
    )

    @api.depends("product_ids")
    def _compute_products_count(self):
        product_brand = self.env["product.template"]
        groups = product_brand.read_group(
            [("product_brand_id", "in", self.ids)],
            ["product_brand_id"],
            ["product_brand_id"],
            lazy=False,
        )
        data = {group["product_brand_id"][0]: group["__count"] for group in groups}
        for brand in self:
            brand.products_count = data.get(brand.id, 0)

    @api.depends("brand_model_ids")
    def _compute_models_count(self):
        _logger.debug("Enter _compute_models_count")
        brand_model = self.env["product.model"]
        _logger.debug("Brand_model:")
        _logger.debug(brand_model)
        groups = brand_model.read_group(
            [("product_mybrand_id", "in", self.ids)],
            ["product_mybrand_id"],
            ["product_mybrand_id"],
            lazy=False,
        )
        _logger.debug("Groups: %s",groups,exc_info=1)

        data = {group["product_mybrand_id"][0]: group["__count"] for group in groups}
        for model in self:
            model.models_count = data.get(model.id, 0)




