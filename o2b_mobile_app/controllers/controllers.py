from odoo import http,SUPERUSER_ID
from odoo.addons.web.controllers.main import Home
from odoo.http import request
import json
import datetime
from datetime import date 
from datetime import datetime
import logging
from lxml import etree, html

_logger = logging.getLogger(__name__)

class O2bMobileController(Home):

    @http.route('/technician/dropdown', type='http',methods= ['POST','GET'], auth='public', website=True, csrf=True)
    def technician_dropdown(self, **kw):
        client_secret = kw.get("client_secret") if kw.get("client_secret") else False
        database_secret = request.env['ir.config_parameter'].sudo().get_param('database.secret')
        if client_secret == database_secret:
            all_employee_partner = request.env['hr.employee'].sudo().search([]).mapped('address_home_id').mapped('id')
            technician_dropdown = request.env['res.partner'].sudo().search([('is_technician','=',True),('id','in',all_employee_partner)]).mapped('name')
            graph_result = []

            for technician in technician_dropdown:
                dcts = {}
                dcts['label'] = str(technician)
                dcts['value'] = str(technician)
                dcts['color'] = 'black'

                graph_result.append(dcts)
            final_view = {'technician_dropdown' : graph_result}
            return json.dumps(final_view)

    @http.route('/ticket/dropdown', type='http',methods= ['POST','GET'], auth='public', website=True, csrf=True)
    def ticket_dropdown(self, **kw):
        client_secret = kw.get("client_secret") if kw.get("client_secret") else False
        database_secret = request.env['ir.config_parameter'].sudo().get_param('database.secret')
        if client_secret == database_secret:
            ticket_dropdown = request.env['project.task'].sudo().search([('stage_id', '=', 'New')]).mapped('name')
            # print("check*********",ticket_dropdown[0].stage_id)
            graph_result = []

            for ticket in ticket_dropdown:
                dcts = {}
                dcts['label'] = str(ticket)
                dcts['value'] = str(ticket)
                dcts['color'] = 'black'

                graph_result.append(dcts)
            final_view = {'ticket_dropdown' : graph_result}
            return json.dumps(final_view)

    @http.route('/show/ticket/detail', type='http',methods= ['POST','GET'], auth='public', website=True, csrf=True)
    def show_ticket_detail(self, **kw):
        client_secret = kw.get("client_secret") if kw.get("client_secret") else False
        selected_ticket = kw.get("selected_ticket_name") if kw.get("selected_ticket_name") else False
        work_sheet_barcode_number = kw.get("work_sheet_barcode_number") if kw.get("work_sheet_barcode_number") else False
        database_secret = request.env['ir.config_parameter'].sudo().get_param('database.secret')
        if client_secret == database_secret:
            _logger.info("I am in*********************************************************")
            graph_result = []
            # ids = kw.get("ids") if kw.get("ids") else False
            if work_sheet_barcode_number != 'false':
                search_ticket = request.env['project.task'].sudo().search([('barcode_gen','=',work_sheet_barcode_number)])[0]
            elif selected_ticket:
                search_ticket = request.env['project.task'].sudo().search([('name','=',selected_ticket)])[0]
            else:
                search_ticket = request.env['project.task'].sudo().browse(15)
            _logger.info("search_ticket@@@@@@@@@@@@@@@*********************************************************")
            _logger.info(search_ticket)
            if search_ticket:
                for ticket_detail in search_ticket:
                    dcts = {}
                    dcts['task_name'] = ticket_detail.name if ticket_detail.name else ""
                    dcts['task_id'] = ticket_detail.id if ticket_detail.id else False
                    dcts['customer_name'] = ticket_detail.partner_id.name if ticket_detail.partner_id else ""
                    dcts['customer_phone'] = ticket_detail.partner_phone if ticket_detail.partner_phone else ""
                    dcts['project_name'] = ticket_detail.project_id.name if ticket_detail.project_id else ""
                    # print("ticket_detail.planned_date_begin++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>",ticket_detail.planned_date_begin)
                    dcts['planned_date'] = str(ticket_detail.planned_date_begin) if ticket_detail.planned_date_begin else ""
                    # print("ticket_detail.date_assign++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>",ticket_detail.date_assign)
                    if ticket_detail.work_type == 'internalrepair':
                        work = 'Internal Repair'
                    elif ticket_detail.work_type == 'externalrepair':
                        work = 'External Repair'
                    dcts['work_type'] = work if ticket_detail.work_type else ""
                    doc = html.fromstring(ticket_detail.description)
                    words = u" ".join(doc.xpath("//text()")).split()
                    msg =""
                    if len(words):
                        msg = '%s' % " ".join(words)
                        # message_list.append(msg)
                    dcts['ticket_description'] = msg if ticket_detail.description else ""
                    dcts['assigned_date'] = str(ticket_detail.date_assign) if ticket_detail.date_assign else ""
                    graph_result.append(dcts)
            final_view = {"graph_result": graph_result}
            return json.dumps(final_view)

    @http.route('/create/product/line', type='json',methods= ['POST','GET'], auth='public', website=True, csrf=True)
    def create_product_line(self, **kw):
        client_secret = kw.get("client_secret") if kw.get("client_secret") else False
        barcode_num = kw.get("barcode_num") if kw.get("barcode_num") else False
        task_num = kw.get("task_num") if kw.get("task_num") else False
        database_secret = request.env['ir.config_parameter'].sudo().get_param('database.secret')
        _logger.info("barcode ====== >> ")
        _logger.info(barcode_num)
        if client_secret == database_secret and barcode_num:
            graph_result = []
            # ids = kw.get("ids") if kw.get("ids") else False
            search_product_product = request.env['product.product'].with_user(SUPERUSER_ID).search([('barcode','=',barcode_num)],limit=1)
            _logger.info("product ====== >> ")
            _logger.info(search_product_product)
            search_product_template = request.env['product.template'].with_user(SUPERUSER_ID).search([('barcode','=',barcode_num)],limit=1)
            _logger.info(search_product_template)
            if search_product_template:
                search_product = search_product_template.product_variant_id
                search_ticket = request.env['project.task'].sudo().browse(int(task_num))
                # For adding product in smart button
                search_product.with_context(fsm_task_id=task_num).with_user(SUPERUSER_ID).set_fsm_quantity(search_product.sudo().fsm_quantity + 1)
                
                product_line_details = {
                    'task_id': int(task_num),
                    'product_name': search_product.id,
                    'product_quant': 1,
                }
                product_line = request.env['product.detail.line'].sudo().create(product_line_details)
                # if search_product:
                #     for product_detail in search_product:
                dcts = {}
                dcts['task_num'] = task_num if task_num else ""
                graph_result.append(dcts)
                final_view = {"graph_result": graph_result}
                return json.dumps(final_view)


    @http.route('/show/product/detail', type='http',methods= ['POST','GET'], auth='public', website=True, csrf=True)
    def show_product_detail(self, **kw):
        graph_result = []

        client_secret = kw.get("client_secret") if kw.get("client_secret") else False
        task_num = kw.get("task_num") if kw.get("task_num") else False
        _logger.info("task_num@@@@@@@@@@@@@@@*********************************************************")
        _logger.info(task_num)
        database_secret = request.env['ir.config_parameter'].sudo().get_param('database.secret')
        search_ticket = request.env['project.task'].sudo().browse(int(task_num))
        _logger.info("search_ticket@@@@@@@@@@@@@@@*********************************************************")
        _logger.info(search_ticket)
        ir_url_obj = request.env['ir.config_parameter'].sudo().search([('key','=','web.base.url')] ,limit=1)
        if client_secret == database_secret and search_ticket:
            for product_detail in search_ticket.product_detail_line:
                dcts = {}
                dcts['id'] = str(product_detail.id)
                dcts['product_name'] = product_detail.product_name.name
                dcts['product_quantity'] = product_detail.product_quant
                graph_result.append(dcts)
        _logger.info("graph_result@@@@@@@@@@@@@@@*********************************************************")
        _logger.info(graph_result)

        final_view = {"graph_result": graph_result}
        return json.dumps(final_view)

    @http.route('/update/product/line', type='json',methods= ['POST','GET'], auth='public', website=True, csrf=True)
    def update_product_line(self, **kw):
        client_secret = kw.get("client_secret") if kw.get("client_secret") else False
        line_id = kw.get("line_id") if kw.get("line_id") else False
        quantity = kw.get("quantity") if kw.get("quantity") else False
        task_num = kw.get("task_num") if kw.get("task_num") else False
        database_secret = request.env['ir.config_parameter'].sudo().get_param('database.secret')
        if client_secret == database_secret and line_id:
            graph_result = []
            search_product_line = request.env['product.detail.line'].sudo().browse(int(line_id))

            task_obj = search_product_line.task_id
            product_obj = search_product_line.product_name
            if search_product_line.product_quant < quantity:
                product_obj.with_context(fsm_task_id=task_obj.id).with_user(SUPERUSER_ID).fsm_add_quantity()
                search_product_line.product_quant = quantity
            elif search_product_line.product_quant > quantity:
                product_obj.with_context(fsm_task_id=task_obj.id).with_user(SUPERUSER_ID).fsm_remove_quantity()
                search_product_line.product_quant = quantity

            # search_product_line.product_quant = quantity
            dcts = {}
            dcts['line_id'] = line_id if line_id else ""
            graph_result.append(dcts)
            final_view = {"graph_result": graph_result}
            return json.dumps(final_view)

    @http.route('/timesheet/line/remove', type='json', auth='public')
    def timesheet_line_remove(self, **kw):
        line_id = kw.get("line_id") if kw.get("line_id") else False 
        timesheet_line = request.env['account.analytic.line'].sudo().browse(int(line_id))
        return timesheet_line.unlink()

    @http.route('/product/line/remove', type='json', auth='public')
    def product_line_remove(self, **kw):
        line_id = kw.get("line_id") if kw.get("line_id") else False 
        product_line = request.env['product.detail.line'].sudo().browse(int(line_id))
        task_obj = product_line.task_id
        product_obj = product_line.product_name
        test = product_obj.with_context(fsm_task_id=task_obj.id).with_user(SUPERUSER_ID).fsm_remove_quantity()
        while(test != None):
            test = product_obj.with_context(fsm_task_id=task_obj.id).with_user(SUPERUSER_ID).fsm_remove_quantity()
        return product_line.unlink()



    @http.route('/show/timesheet/line', type='http',methods= ['POST','GET'], auth='public', website=True, csrf=True)
    def show_timesheet_detail(self, **kw):
        graph_result = []

        client_secret = kw.get("client_secret") if kw.get("client_secret") else False
        task_num = kw.get("task_num") if kw.get("task_num") else False
        _logger.info("task_num@@@@@@@@@@@@@@@*********************************************************")
        _logger.info(task_num)
        database_secret = request.env['ir.config_parameter'].sudo().get_param('database.secret')
        search_ticket = request.env['project.task'].sudo().browse(int(task_num))
        _logger.info("search_ticket@@@@@@@@@@@@@@@*********************************************************")
        _logger.info(search_ticket)
        ir_url_obj = request.env['ir.config_parameter'].sudo().search([('key','=','web.base.url')] ,limit=1)
        if client_secret == database_secret and search_ticket:
            for timesheet_detail in search_ticket.timesheet_ids:
                dcts = {}
                dcts['id'] = str(timesheet_detail.id)
                dcts['date'] = datetime.strptime(str(timesheet_detail.date), '%Y-%m-%d').strftime('%m/%d/%Y')
                dcts['employee'] = timesheet_detail.employee_id.name
                dcts['description'] = timesheet_detail.name
                dcts['duration'] = str(str(int(timesheet_detail.unit_amount)) + ':' + str(int((timesheet_detail.unit_amount)*60)%60))
                graph_result.append(dcts)
        _logger.info("graph_result@@@@@@@@@@@@@@@*********************************************************")
        _logger.info(graph_result)
        final_view = {"graph_result": graph_result}
        return json.dumps(final_view)

    @http.route('/create/timesheet/line', type='json',methods= ['POST','GET'], auth='public', website=True, csrf=True)
    def create_timesheet_line(self, **kw):
        client_secret = kw.get("client_secret") if kw.get("client_secret") else False
        timesheet = kw.get("timesheet") if kw.get("timesheet") else False
        task_num = kw.get("task_num") if kw.get("task_num") else False
        date = kw.get("date") if kw.get("date") else False
        description = kw.get("description") if kw.get("description") else False
        technician = kw.get("technician") if kw.get("technician") else False
        duration = kw.get("duration") if kw.get("duration") else False
        date = datetime.strptime(date, "%d/%m/%Y").date()
        database_secret = request.env['ir.config_parameter'].sudo().get_param('database.secret')
        if client_secret == database_secret:
            graph_result = []
            # ids = kw.get("ids") if kw.get("ids") else False
            _logger.info("duration@@@@@@@@@@@@@@@*********************************************************")
            _logger.info(duration)
            search_technician = request.env['res.partner'].sudo().search([('name','=',technician)])[0]
            search_ticket = request.env['project.task'].sudo().browse(int(task_num))
            search_employee = request.env['hr.employee'].sudo().search([('address_home_id','=',search_technician.id)])[0]
            account_id = search_ticket.project_id.analytic_account_id.id
            product_uom_id = 6
            if search_ticket.sale_line_id:
                product_uom_id = search_ticket.sale_line_id.product_uom.id
            account_analytic_line = {
                'task_id': int(task_num),
                'date': date,
                'name': description,
                'unit_amount':float(duration),
                'employee_id':search_employee.id,
                'account_id': account_id,
                'timesheet_invoice_type':'billable_time',
                'product_uom_id':product_uom_id,
            }
            product_line = request.env['account.analytic.line'].sudo().create(account_analytic_line)
            # if search_product:
            #     for product_detail in search_product:
            dcts = {}
            dcts['task_num'] = task_num if task_num else ""
            graph_result.append(dcts)
            final_view = {"graph_result": graph_result}
            return json.dumps(final_view)