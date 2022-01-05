# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class ReportCheckbookRegisterXlsx(models.AbstractModel):

    _name = 'report.qb_checkbook_register.report_checkbook_reg_xlsx'
    _description = 'Checkbook Register Report Xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    
    def generate_xlsx_report(self, workbook, data, report):
        domain_search = []
        date_from = date_to = fields.Date.today()
        check_obj = self.env['account.payment']             
        date_from = fields.Date.from_string(data['form'].get('date_from')) or fields.Date.today()
        date_to = fields.Date.from_string(data['form'].get('date_to')) or fields.Date.today()
        if date_from and date_to:
            date_from_display = date_from.strftime("%m-%d-%Y")
            date_to_display = date_to.strftime("%m-%d-%Y")
            if date_to < date_from:
                raise UserError(_('Your date from is greater than date to.')) 
        company_id = data['form'].get('company_id', False)
        company_id = company_id and company_id[0] or None
        date_domain = [('company_id','=',company_id)]
        date_domain += [('payment_date','>=',date_from.strftime("%Y-%m-%d 00:00:00"))]
        date_domain += [('payment_date','<=',date_to.strftime("%Y-%m-%d 23:59:59"))]
        date_domain += [('state','not in',['draft','sent','cancelled'])]
        date_domain += [('payment_method_id.name','=','Checks')]
        bold_cust = workbook.add_format({'bold': True,'underline': 1})
        bold = workbook.add_format({'bold': True,'font_size': 13})
        subtitle = workbook.add_format({'bold': True,'font_size': 15})
        title = workbook.add_format({'bold': True,'font_size': 20})
        checks = check_obj.search(date_domain) 
        sheet = workbook.add_worksheet('Checkbook')
        sheet.write(0, 1, 'Checkbook Register', title)
        sheet.write(1, 1, 'Date From: ', bold)
        sheet.write(1, 2, date_from_display, bold)      
        sheet.write(1, 4, 'Date To: ', bold)
        sheet.write(1, 5, date_to_display, bold)
        i,j = 0,0
        subtotal = 0
        sheet.write(4, 0, 'Check #', bold_cust)
        sheet.write(4, 1, 'Payment Date', bold_cust)
        sheet.write(4, 2, 'Name', bold_cust)
        sheet.write(4, 3, 'Journal', bold_cust)
        sheet.write(4, 4, 'Payee #', bold_cust)
        sheet.write(4, 5, 'Amount', bold_cust)
                        
        for check in checks:  
            subtotal += check.amount        
            sheet.write(i+j+5, 0, check.check_number)
            sheet.write(i+j+5, 1, check.payment_date)
            sheet.write(i+j+5, 2, check.name)
            sheet.write(i+j+5, 3, check.journal_id.name)
            sheet.write(i+j+5, 4, check.partner_id.name)
            sheet.write(i+j+5, 5, check.amount)
            i += 1
            j += 1
        sheet.write(i+j+5, 4, 'TOTAL: ', bold_cust)
        sheet.write(i+j+5, 5, subtotal, bold_cust)

          
class CheckbookRegisterReport(models.AbstractModel):

    _name = 'report.qb_checkbook_register.report_checkbook_reg'
    _description = 'Checkbook Register Report'
            
    @api.model
    def _get_report_values(self, docids, data=None):
        domain_search = []
        date_from = date_to = fields.Date.today()
        check_obj = self.env['account.payment']             
        date_from = fields.Date.from_string(data['form'].get('date_from')) or fields.Date.today()
        date_to = fields.Date.from_string(data['form'].get('date_to')) or fields.Date.today()
        if date_from and date_to:
            date_from_display = date_from.strftime("%m-%d-%Y")
            date_to_display = date_to.strftime("%m-%d-%Y")
            if date_to < date_from:
                raise UserError(_('Your date from is greater than date to.')) 
        company_id = data['form'].get('company_id', False)
        company_id = company_id and company_id[0] or None
        date_domain = [('company_id','=',company_id)]
        date_domain += [('payment_date','>=',date_from.strftime("%Y-%m-%d 00:00:00"))]
        date_domain += [('payment_date','<=',date_to.strftime("%Y-%m-%d 23:59:59"))]
        date_domain += [('state','not in',['draft','sent','cancelled'])]
        date_domain += [('payment_method_id.name','=','Checks')]
        checks = check_obj.search(date_domain)                     
        return {
            'doc_ids': checks.ids,
            'doc_model': 'account.payment',
            'data': data['form'],
            'docs': checks,
            'date_from':date_from.strftime("%m-%d-%Y") if date_from else False,
            'date_to':date_to.strftime("%m-%d-%Y") if date_to else False,
        }