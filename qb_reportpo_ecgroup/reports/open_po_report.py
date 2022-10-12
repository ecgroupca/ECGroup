# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class OpenPurchasesXlsx(models.AbstractModel):

    _name = 'report.qb_reportpo_ecgroup.report_open_po_xlsx'
    _description = 'Open Purchases Report Xlsx'
    _inherit = 'report.report_xlsx.abstract'


    def generate_xlsx_report(self, workbook, data, report):
        domain_search = []
        purchase_obj = self.env['purchase.order']        
        date_from = fields.Date.from_string(data['form'].get('date_from')) or fields.Date.today()
        date_to = fields.Date.from_string(data['form'].get('date_to')) or fields.Date.today()
        date_from_display = date_from.strftime("%m-%d-%Y")
        date_to_display = date_to.strftime("%m-%d-%Y")
        partner_ids = data['form'].get('partner_ids', False)
        company_id = data['form'].get('company_id', False)
        company_id = company_id and company_id[0] or None
        domain_search = [('date_order','>=',date_from.strftime("%Y-%m-%d 00:00:00")),
                         ('date_order','<=',date_to.strftime("%Y-%m-%d 23:59:59")),
                         ('state','=','purchase')]
        if partner_ids:
            domain_search.append(('partner_id','in',partner_ids))
        if company_id:
            domain_search.append(('company_id','=',company_id))        
        po_ids = self.env['purchase.order'].search(domain_search,order="date_order asc")  
        sheet = workbook.add_worksheet('Open Purchases')
        bold = workbook.add_format({'bold': True})
        sheet.write(0, 1, 'Open Purchases Report', bold)
        sheet.write(1, 1, 'Date From: ', bold)
        sheet.write(1, 2, date_from_display, bold)      
        sheet.write(1, 4, 'Date To: ', bold)
        sheet.write(1, 5, date_to_display, bold)
        i,j = 0,0
        vendors = {}
        for po in po_ids:
            vendor_name = "%s_%s"%(po.partner_id.name.replace(" ","_"),po.partner_id.id)
            if vendor_name in vendors:
                vendors[vendor_name].append(po)
            else:
                vendors.update({vendor_name:[po]})     
        for vendor in vendors.keys():
            j+=2       
            sheet.write(i+j+4, 1, 'Vendor: ', bold)
            sheet.write(i+j+4, 2, vendor, bold)
            sheet.write(i+j+5, 0, 'PO#', bold)
            sheet.write(i+j+5, 1, 'Date', bold)
            sheet.write(i+j+5, 2, 'Sidemark (SO)', bold)
            sheet.write(i+j+5, 3, 'Required', bold)
            sheet.write(i+j+5, 4, 'Order QTY', bold)
            sheet.write(i+j+5, 5, 'Received QTY', bold)
            sheet.write(i+j+5, 6, 'Item #', bold)
            sheet.write(i+j+5, 7, 'Item', bold)
            sheet.write(i+j+5, 8, 'Description', bold)
            sheet.write(i+j+5, 9, 'Vendor Comments', bold)
            
            for purchase in vendors[vendor]: 
                i+=1            
                sheet.write(j+i+5, 0, purchase.name, bold)
                sheet.write(j+i+5, 1, purchase.date_order.strftime("%m-%d-%Y"))               
                sheet.write(j+i+5, 2, purchase.partner_ref)
                for line in purchase.order_line:
                    sheet.write(j+i+5, 3, line.date_planned and line.date_planned.strftime('%m/%d/%y') or '')
                    sheet.write(j+i+5, 4, line.product_qty)
                    sheet.write(j+i+5, 5, line.qty_received)
                    sheet.write(j+i+5, 6, line.product_id.default_code)
                    sheet.write(j+i+5, 7, line.product_id.name)
                    sheet.write(j+i+5, 8, line.name.split('\n', 2)[:2][0])
                    i+=1

class ReportOpenPOReport(models.AbstractModel):

    _name = 'report.qb_reportpo_ecgroup.report_open_po'
    _description = 'Open PO report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = fields.Date.from_string(data['form'].get('date_from')) or fields.Date.today()
        date_to = fields.Date.from_string(data['form'].get('date_to')) or fields.Date.today()
        partner_ids = data['form'].get('partner_ids', False)
        company_id = data['form'].get('company_id', False)
        company_id = company_id and company_id[0] or None
        domain_search = [('date_order','>=',date_from.strftime("%Y-%m-%d 00:00:00")),
                         ('date_order','<=',date_to.strftime("%Y-%m-%d 23:59:59")),
                         ('state','=','purchase')]
        if partner_ids:
            domain_search.append(('partner_id','in',partner_ids))
        if company_id:
            domain_search.append(('company_id','=',company_id))        
        po_ids = self.env['purchase.order'].search(domain_search,order="date_order asc")
        
        sm = {}
        for po in po_ids:
            vendor_name = "%s_%s"%(po.partner_id.name.replace(" ","_"),po.partner_id.id)
            
            if vendor_name in sm:
                sm[vendor_name]['data'].append(po)
            else:
                sm.update({vendor_name:{'name':po.partner_id.name,'ref':po.partner_id.ref,'data':[po]}})
        
        return {
            'doc_ids': po_ids.ids,
            'doc_model': 'purchase.order',
            'data': data['form'] if not docids else data,
            'docs': po_ids,
            'sm':sm,
            'date_from':date_from.strftime("%d-%m-%Y") if date_from else False,
            'date_to':date_to.strftime("%d-%m-%Y") if date_to else False,
        }