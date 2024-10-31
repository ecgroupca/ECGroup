# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class ReportACHPaymentsXlsx(models.AbstractModel):

    _name = 'report.qb_ach_payments.report_ach_payments_xlsx'
    _description = 'ACH Payments Xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    
    def generate_xlsx_report(self, workbook, data, report):
        domain_search = []
        date_from = date_to = fields.Date.today()
        ach_obj = self.env['account.payment']
        pmt_method = self.env['account.payment.method']
        dom = [('name','=','ACH')]
        methods = pmt_method.search(dom)
        if not methods:
            #generate the 'ACH' account.payment.method
            error = pmt_method.create({'name':'ACH','code':'ACH','payment_type':'outbound'})           
            if not error:
                raise UserError(_('Payment type ACH not created.'))            
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
        date_domain += [('state','not in',['draft','cancelled'])]
        date_domain += [('payment_method_id.name','=','ACH')]
        
        bold_cust = workbook.add_format({'bold': True,'underline': 1})
        bold = workbook.add_format({'bold': True,'font_size': 13})
        subtitle = workbook.add_format({'bold': True,'font_size': 15})
        title = workbook.add_format({'bold': True,'font_size': 20})
        pmts = ach_obj.search(date_domain) 
        sheet = workbook.add_worksheet('ACH Payments')
        sheet.write(0, 1, 'ACH Payments', title)
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
                        
        for pmt in pmts:  
            subtotal += pmt.amount        
            sheet.write(i+j+5, 0, pmt.check_number)
            sheet.write(i+j+5, 1, pmt.payment_date)
            sheet.write(i+j+5, 2, pmt.name)
            sheet.write(i+j+5, 3, pmt.journal_id.name)
            sheet.write(i+j+5, 4, pmt.partner_id.name)
            sheet.write(i+j+5, 5, pmt.amount)
            i += 1
            j += 1
        sheet.write(i+j+5, 4, 'TOTAL: ', bold_cust)
        sheet.write(i+j+5, 5, subtotal, bold_cust)
        