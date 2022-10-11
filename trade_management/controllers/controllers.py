# -*- coding: utf-8 -*-
# from odoo import http


# class TradeManagement(http.Controller):
#     @http.route('/trade_management/trade_management/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/trade_management/trade_management/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('trade_management.listing', {
#             'root': '/trade_management/trade_management',
#             'objects': http.request.env['trade_management.trade_management'].search([]),
#         })

#     @http.route('/trade_management/trade_management/objects/<model("trade_management.trade_management"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('trade_management.object', {
#             'object': obj
#         })
