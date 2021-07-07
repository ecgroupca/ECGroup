# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class OpenSalesReport(models.AbstractModel):

    _name = 'report.qb_opensales_reports.report_opensales'
    _description = 'Open Sales Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        domain_search = []
        date_from = date_to = fields.Date.today()
        print_selected = True      
        if not docids:
            print_selected = data['form'].get('print_selected') 
            date_from = fields.Date.from_string(data['form'].get('date_from')) or fields.Date.today()
            date_to = fields.Date.from_string(data['form'].get('date_to')) or fields.Date.today()
            showroom = data['form'].get('showroom', False)
            selected_sales = data['form'].get('sale_ids', False)            
            if not print_selected:
                #domain_search = [('date','>=',date_from.strftime("%m/%d/%Y 00:00:00")),('date','<=',date_to.strftime("%m/%d/%Y 23:59:59"))]
                domain_search = ['|',('open_production','!=',False),('open_shipment','!=',False),('date_order','>=',date_from.strftime("%Y-%m-%d 00:00:00")),('date_order','<=',date_to.strftime("%Y-%m-%d 23:59:59"))]
                if showroom:
                    domain_search.append(('sale_id.team_id','in',showroom))
            else:
                date_from = date_to = False
                if not selected_sales:
                    raise UserError(_("No sales records selected!"))
                domain_search.append(('id','in',selected_sales))
        else :
            date_from = date_to = False
            domain_search = [('id','in',docids)]
        
        sale_orders = self.env['sale.order'].search(domain_search)
        sales = {}
        for sale in sale_orders:
            team_name = 'No_Name'
            if sale.team_id:
                team_name = sale.team_id.name.replace(" ","_")           
            if team_name in sales:
                sales[team_name].append(sale)
            else:
                sales.update({team_name:[sale]})
        
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