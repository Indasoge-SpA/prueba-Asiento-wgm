 #-*- coding: utf-8 -*-

# Copyright (c) 2018 Daniel Campos <danielcampos@avanzosc.es> - Avanzosc S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from .common import CommonCase


class TestProductModel(CommonCase):
    def test_products_count(self):
        self.assertEqual(
            self.product_model.products_count, 0, "Error product count does not match"
        )
        self.product.product_model_id = self.product_model.id
        self.assertEqual(
            self.product_model.products_count, 1, "Error product count does not match"
        )
