# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class UnbilledSalesReport(models.AbstractModel):

    _name = 'report.qb_unbilled_closed_sales.report_closed_unbilled_sales'
    _description = 'Unbilled Shipped Sales Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        domain_search = []
        date_from = date_to = fields.Date.today()
        sale_obj = self.env['sale.order']        
        if not docids:
            date_from = fields.Date.from_string(data['form'].get('date_from'))
            date_to = fields.Date.from_string(data['form'].get('date_to'))
            showroom = data['form'].get('showroom', False)
            company_id = data['form'].get('company_id', False)
            company_id = company_id and company_id[0] or None        
            domain = [('company_id','=',company_id),('state','not in',['draft','cancel','sent'])]
            domain += [('invoice_status','=','to invoice'),('trans_shipped_date','!=',False)]
            if date_from and date_to:
                domain.append(('date_order','>=',date_from.strftime("%Y-%m-%d 00:00:00")))
                domain.append(('date_order','<=',date_to.strftime("%Y-%m-%d 23:59:59")))
            sales_from_to = sale_obj.search(domain)
            if showroom:
                domain.append(('team_id','in',showroom))
        else :
            date_from = date_to = False
            domain = [('id','in',docids)]
        sale_orders = sale_obj.search(domain)      
        sales = {}
        for sale in sale_orders:
            team_name = 'No_Name'
            if sale.team_id:
                team_name = sale.team_id.name.replace(" ","_")           
            if team_name in sales:
                sales[team_name].append(sale)
            else:
                sales.update({team_name:[sale]})      
           
        return {
            'doc_ids': sale_orders.ids,
            'doc_model': 'sale.order',
            'data': data['form'] if not docids else data,
            'docs': sale_orders,
            'sm':sales,
            'date_from':date_from.strftime("%d-%m-%Y") if date_from else False,
            'date_to':date_to.strftime("%d-%m-%Y") if date_to else False,
        }