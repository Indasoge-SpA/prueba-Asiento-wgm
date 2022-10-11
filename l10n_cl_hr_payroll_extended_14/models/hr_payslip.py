import base64, os
from io import BytesIO
from datetime import datetime
from tempfile import gettempdir
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
import logging 


class HrPayslipRule(models.Model):
	_inherit = 'hr.salary.rule'

	libro = fields.Boolean(string="Aparece en el libro", default=False) 


class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'


	def print_payroll_xlsx(self):
		for rec in self:
			cuurent_date = datetime.strftime(datetime.now(), tools.DEFAULT_SERVER_DATE_FORMAT)
			cuurent_time = datetime.strftime(datetime.now(), '%I:%M %p')
			if not rec.slip_ids:
				raise ValidationError(_("Payslip batch have no payslips."))
			#ESTE CASO MUESTRA SOLO LAS REGLAS QUE APAREZCAN EN LAS LIQUIDACIONES. NO NOS GUSTA PORQUE ES MUY DINAMICO
#            self._cr.execute('''SELECT id, name FROM hr_salary_rule
#                                WHERE id in (
#                                select salary_rule_id from hr_payslip_line
#                                    where slip_id in (select id from hr_payslip where payslip_run_id = %s)
#                                ) ORDER BY sequence
#                            ''' %(rec.id))

			self._cr.execute('''SELECT id, name FROM hr_salary_rule
								WHERE libro = True ORDER BY sequence
							''' )

			datas = self._cr.fetchall() 
			
			

			exist_salary_rules = [rules[0] for rules in datas]
			exist_salary_rules_name = [rules[1] for rules in datas]
			if not exist_salary_rules:
				raise ValidationError(_("Please check payslip have no salary rules.\n"
										"Payslips may be not a computed."))

			all_payslip_data = []
			for slip_rec in rec.slip_ids:
				try:
					name = slip_rec.employee_id.last_name +' ' +slip_rec.employee_id.mothers_name + ' ' +slip_rec.employee_id.firstname + ' ' +slip_rec.employee_id.middle_name
				except:
					try:
						name = slip_rec.employee_id.last_name + ' ' +slip_rec.employee_id.mothers_name + ' ' +slip_rec.employee_id.firstname
					except:
						name = slip_rec.employee_id.last_name +  ' ' +slip_rec.employee_id.firstname			

				payslip_data = {'employee_name': name or '',  
								'employee_rut': slip_rec.employee_id.identification_id or '',
								#'employee_analytic_account': slip_rec.contract_id.analytic_account_id.code or '01'}
								'employee_analytic_account': '01'}
				for payslip_line in slip_rec.line_ids:
					if payslip_line.salary_rule_id:
						payslip_data.update({payslip_line.salary_rule_id.id: float(payslip_line.total)})
				all_payslip_data.append(payslip_data)

			report_col_name = 'payrll_batch_report_title'
			workbook = xlsxwriter.Workbook(os.path.join(gettempdir(), 'payrll_batch_report.xlsx'))
			worksheet = workbook.add_worksheet(_('Payslip Batch'))

			worksheet.set_paper(9)
			worksheet.set_portrait()
			worksheet.fit_to_pages(1, 0)

			merge_format = workbook.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'font_size': 10})
			merge_format_header = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 18})
			header_rule_format_left = workbook.add_format({'bold': True, 'align': 'left', 'valign': 'bottom', 'font_size': 10,
														   'text_wrap': True, 'bottom': 5})
			header_rule_format_right = workbook.add_format({'bold': True, 'align': 'right', 'valign': 'bottom',
															'font_size': 10, 'text_wrap': True, 'bottom': 5})

			header_format_right = workbook.add_format({'bold': True, 'align': 'right', 'valign': 'vcenter', 'font_size': 10})
			header_format_right.set_bottom(2)

			emp_data_format = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'font_size': 10})
			data_format = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'font_size': 10})

			data_format_total = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'font_size': 10,
													 'bottom': 2, 'top': 2})

			# header_format.set_border(1)
			line_format = workbook.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'font_size': 10})
			worksheet.set_header('&R' + '&P' + ' of ' + '&P')

			row = 0
			col = 0

			# Date 1st line print date........
			from_cell = xl_rowcol_to_cell(row, col)
			to_cell = xl_rowcol_to_cell(row, col)
			worksheet.write(str(from_cell) + ':' + str(to_cell), str(cuurent_date), merge_format)

			row += 1
			from_cell = xl_rowcol_to_cell(row, col)
			to_cell = xl_rowcol_to_cell(row, col)
			worksheet.write(str(from_cell) + ':' + str(to_cell), str(cuurent_time), merge_format)


			# Header printing........
			row += 1
			worksheet.repeat_rows(0, 3)
			from_cell = xl_rowcol_to_cell(row, col)
			col = 10
			to_cell = xl_rowcol_to_cell(row, len(exist_salary_rules_name))
			worksheet.set_row(2, 20, merge_format_header)
			worksheet.merge_range(str(from_cell) + ':' + str(to_cell), 'Libro de Remuneraciones', merge_format_header)

			row += 1
			col = 0
			counter = 0
			final_total_dict = {'total': 'Total'}
			worksheet.set_row(row, 35, merge_format_header)
			for payslip_data in all_payslip_data:
				if counter == 0:
					from_cell = xl_rowcol_to_cell(row, col)
					to_cell = xl_rowcol_to_cell(row, col)
					worksheet.write(str(from_cell) + ':' + str(to_cell), 'CC', header_rule_format_left)
					col += 1
					from_cell = xl_rowcol_to_cell(row, col)
					to_cell = xl_rowcol_to_cell(row, col)
					worksheet.write(str(from_cell) + ':' + str(to_cell), 'EMPLEADO', header_rule_format_left)
					col += 1
					from_cell = xl_rowcol_to_cell(row, col)
					to_cell = xl_rowcol_to_cell(row, col)
					worksheet.write(str(from_cell) + ':' + str(to_cell), 'RUT', header_rule_format_left)
					for salary_rule in exist_salary_rules:
						worksheet.set_column(str(from_cell) + ':' + str(to_cell), 14)
						col += 1
						from_cell = xl_rowcol_to_cell(row, col)
						to_cell = xl_rowcol_to_cell(row, col)
						worksheet.write(str(from_cell) + ':' + str(to_cell),
										exist_salary_rules_name[counter], header_rule_format_right)
						counter += 1
					from_cell = xl_rowcol_to_cell(row, col)
					to_cell = xl_rowcol_to_cell(row, col)
					worksheet.set_column(str(from_cell) + ':' + str(to_cell), 14)

				row += 1
				col = 0
				from_cell = xl_rowcol_to_cell(row, col)
				to_cell = xl_rowcol_to_cell(row, col)
				worksheet.write(str(from_cell) + ':' + str(to_cell), payslip_data.get('employee_analytic_account'), emp_data_format)
				col += 1
				from_cell = xl_rowcol_to_cell(row, col)
				to_cell = xl_rowcol_to_cell(row, col)
				worksheet.write(str(from_cell) + ':' + str(to_cell), payslip_data.get('employee_name'), emp_data_format)
				col += 1
				from_cell = xl_rowcol_to_cell(row, col)
				to_cell = xl_rowcol_to_cell(row, col)
				worksheet.write(str(from_cell) + ':' + str(to_cell), payslip_data.get('employee_rut'), emp_data_format)
				for salary_rule_id in exist_salary_rules:
					col += 1
					from_cell = xl_rowcol_to_cell(row, col)
					to_cell = xl_rowcol_to_cell(row, col)
					rule_amt = ("{0:.2f}".format(round(payslip_data.get(salary_rule_id, 0), 2)))
					worksheet.write(str(from_cell) + ':' + str(to_cell), rule_amt, data_format)

					if salary_rule_id in payslip_data.keys():
						final_total_dict.update({salary_rule_id: final_total_dict.get(salary_rule_id, 0) + \
															payslip_data.get(salary_rule_id, 0)})
					else:
						final_total_dict.update({salary_rule_id: final_total_dict.get(salary_rule_id, 0)})

			# For Grand total.......
			row += 1
			col = 2
			from_cell = xl_rowcol_to_cell(row, col)
			to_cell = xl_rowcol_to_cell(row, col)
			worksheet.write(str(from_cell) + ':' + str(to_cell), final_total_dict.get('total'), header_format_right)
			worksheet.set_row(row, 25, data_format)
			for salary_rule_id in exist_salary_rules:
				col += 1
				from_cell = xl_rowcol_to_cell(row, col)
				to_cell = xl_rowcol_to_cell(row, col)
				tot_final = ("{0:.2f}".format(round(final_total_dict.get(salary_rule_id, 0), 2)))
				worksheet.write(str(from_cell) + ':' + str(to_cell), tot_final, data_format_total)

			workbook.close()
			f2 = open(os.path.join(gettempdir(), 'payrll_batch_report.xlsx'), 'rb')
			f_data = f2.read()
			data = base64.encodestring(f_data)
			ctx = dict(self._context)
			ctx.update({'default_attachment': data, 'default_filename': _('Payslip Batch.xlsx')})

			attachement_obj = self.env['attachment.report']
			attachment_id = attachement_obj.create({'attachment': data,
													'filename': 'Payslip Batch.xlsx'})
			return {
				'name': _('Attachment'),
				'res_id': attachment_id.id,
				'view_type': 'form',
				"view_mode": 'form',
				'res_model': 'attachment.report',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'context': ctx,
			}
