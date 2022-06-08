# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class OpenSalesXlsx(models.AbstractModel):

    _name = 'report.qb_opensales_reports.report_opensales_xlsx'
    _description = 'Open Sales Report Xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    
    def generate_xlsx_report(self, workbook, data, report):
        domain_search = []
        sale_obj = self.env['sale.order']        
        print_selected = data['form'].get('print_selected') 
        date_from = fields.Date.from_string(data['form'].get('date_from')) or fields.Date.today()
        date_to = fields.Date.from_string(data['form'].get('date_to')) or fields.Date.today()
        date_from_display = date_from.strftime("%m-%d-%Y")
        date_to_display = date_to.strftime("%m-%d-%Y")
        showroom = data['form'].get('showroom', False)
        company_id = data['form'].get('company_id', False)
        company_id = company_id and company_id[0] or None
        responsible_id = data['form'].get('responsible_id', False)
        responsible_id = responsible_id and responsible_id[0] or None
        selected_sales = data['form'].get('sale_ids', False)
        #domain_search = [('date','>=',date_from.strftime("%m/%d/%Y 00:00:00")),('date','<=',date_to.strftime("%m/%d/%Y 23:59:59"))]
        date_domain = [('company_id','=',company_id),('state','not in',['draft','cancel','sent']),('date_order','>=',date_from.strftime("%Y-%m-%d 00:00:00")),('date_order','<=',date_to.strftime("%Y-%m-%d 23:59:00"))]
        #sales_from_to = sale_obj.search(date_domain)
        #compute open shipments/production for the orders in docids 
        #sales_from_to._compute_open_shipments()               
        domain_search = ['|',('open_shipment','=',True),('inv_bal_due','>=',0.00001)]
        domain_search += date_domain
        if showroom:
            domain_search.append(('team_id','in',showroom))
        if responsible_id:
            domain_search.append(('user_id','=',responsible_id))      
        sale_orders = sale_obj.search(domain_search)      
        sales = {}
        sheet = workbook.add_worksheet('Open Sales')
        bold = workbook.add_format({'bold': True})
        sheet.write(0, 1, 'Open Sales Report', bold)
        sheet.write(1, 1, 'Date From: ', bold)
        sheet.write(1, 2, date_from_display, bold)      
        sheet.write(1, 4, 'Date To: ', bold)
        sheet.write(1, 5, date_to_display, bold)
        i,j = 0,0
        
        for sale in sale_orders:
            team_name = 'No_Name'
            if sale.team_id:
                team_name = sale.team_id.name.replace(" ","_")           
            if team_name in sales:
                sales[team_name].append(sale)
            else:
                sales.update({team_name:[sale]})
        
        for sroom in sales.keys():
            j+=2       
            sheet.write(i+j+4, 1, 'Showroom: ', bold)
            sheet.write(i+j+4, 2, sroom, bold)
            sheet.write(i+j+5, 0, 'Order No.', bold)
            sheet.write(i+j+5, 1, 'Date', bold)
            sheet.write(i+j+5, 2, 'Client PO', bold)
            sheet.write(i+j+5, 3, 'Client', bold)
            sheet.write(i+j+5, 4, 'Total', bold)
            sheet.write(i+j+5, 5, 'Deposits', bold)
            sheet.write(i+j+5, 6, 'Balance', bold)
            sheet.write(i+j+5, 7, 'Responsible', bold)
            sheet.write(i+j+5, 8, 'Status', bold)
            
            for sale in sales[sroom]: 
                i+=1            
                sheet.write(j+i+5, 0, sale.name, bold)
                sheet.write(j+i+5, 1, sale.date_order.strftime("%m-%d-%Y"))
                sheet.write(j+i+5, 2, sale.client_order_ref or '')
                sheet.write(j+i+5, 3, sale.partner_id.name)
                sheet.write(j+i+5, 4, sale.amount_total)
                sheet.write(j+i+5, 5, sale.deposit_total)
                sheet.write(j+i+5, 6, sale.inv_bal_due)
                sheet.write(j+i+5, 7, sale.user_id and sale.user_id.name or '')
                sheet.write(j+i+5, 8, sale.state)
                i+=1
            
class OpenSalesReport(models.AbstractModel):

    _name = 'report.qb_opensales_reports.report_open_sales'
    _description = 'Open Sales Report'
            
    @api.model
    def _get_report_values(self, docids, data=None):
        domain_search = []
        date_from = date_to = fields.Date.today()
        sale_obj = self.env['sale.order']        
        if not docids:
            print_selected = data['form'].get('print_selected') 
            date_from = fields.Date.from_string(data['form'].get('date_from')) or fields.Date.today()
            date_to = fields.Date.from_string(data['form'].get('date_to')) or fields.Date.today()
            showroom = data['form'].get('showroom', False)
            company_id = data['form'].get('company_id', False)
            company_id = company_id and company_id[0] or None
            responsible_id = data['form'].get('responsible_id', False)
            responsible_id = responsible_id and responsible_id[0] or None
            sales_rep_id = data['form'].get('sales_rep_id', False)
            sales_rep_id = sales_rep_id and sales_rep_id[0] or None
            selected_sales = data['form'].get('sale_ids', False)
            if not print_selected:
                #domain_search = [('date','>=',date_from.strftime("%m/%d/%Y 00:00:00")),('date','<=',date_to.strftime("%m/%d/%Y 23:59:59"))]
                date_domain = [('company_id','=',company_id),('state','not in',['draft','cancel','sent']),('date_order','>=',date_from.strftime("%Y-%m-%d 00:00:00")),('date_order','<=',date_to.strftime("%Y-%m-%d 23:59:59"))]
                #sales_from_to = sale_obj.search(date_domain)
                #compute open shipments/production for the orders in docids 
                #sales_from_to._compute_open_shipments()               
                domain_search = ['|',('open_shipment','=',True),('inv_bal_due','>=',0.00001)]
                domain_search += date_domain
                if showroom:
                    domain_search.append(('team_id','in',showroom))
                if responsible_id:
                    domain_search.append(('user_id','=',responsible_id))
                if sales_rep_id:
                    domain_search.append(('sales_rep_id','=',sales_rep_id))
            else:
                date_from = date_to = False
                if not selected_sales:
                    raise UserError(_("No sales records selected!"))
                domain_search.append(('id','in',selected_sales))
        else:
            date_from = date_to = False
            domain_search = [('id','in',docids)]       
        
        sale_orders = sale_obj.search(domain_search)      
        sales = {}
        for sale in sale_orders:
            team_name = 'No Showroom'
            sales_rep_key = sale.sales_rep_id and 'srk_%s'%(sale.sales_rep_id.id) or 'No Sales Rep'
            if sale.team_id:
                team_name = sale.team_id.name.replace(" ","_")           
            if team_name in sales:
                if sales_rep_key in sales[team_name]:
                    sales[team_name][sales_rep_key]['data'].append(sale)
                else:
                    sales[team_name].update({
                       sales_rep_key:{
                       'name':sale.sales_rep_id.name,
                       'id':sale.sales_rep_id.id,
                       'data':[sale]}})
            else:
                sales.update({
                    team_name:{
                        sales_rep_key:{
                            'name':sale.sales_rep_id.name,
                            'id':sale.sales_rep_id.id,
                            'data':[sale]}}})   
                     
        _logger.info("\nFinal : %s\n"%(sales))        
        return {
            'doc_ids': sale_orders.ids,
            'doc_model': 'sale.order',
            'data': data['form'] if not docids else data,
            'docs': sale_orders,
            'sm':sales,
            'date_from':date_from.strftime("%d-%m-%Y") if date_from else False,
            'date_to':date_to.strftime("%d-%m-%Y") if date_to else False,
        }