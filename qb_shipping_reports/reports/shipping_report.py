# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ReportshippingReport(models.AbstractModel):

    _name = 'report.qb_shipping_reports.report_shipping'
    _description = 'Shipping report'
    
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
            selected_moves = data['form'].get('stock_move_ids', False)
            
            if not print_selected:
                #domain_search = [('date','>=',date_from.strftime("%m/%d/%Y 00:00:00")),('date','<=',date_to.strftime("%m/%d/%Y 23:59:59"))]
                domain_search = [('shipped_date','>=',date_from.strftime("%Y-%m-%d 00:00:00")),('shipped_date','<=',date_to.strftime("%Y-%m-%d 23:59:59"))]
                if showroom:
                    domain_search.append(('sale_id.team_id','in',showroom))
            else:
                date_from = date_to = False
                if not selected_moves:
                    raise UserError(_("No shipping records selected!"))
                domain_search.append(('id','in',selected_moves))
        else :
            date_from = date_to = False
            domain_search = [('id','in',docids)]
        
        stock_moves = self.env['stock.move'].search(domain_search)
        sm = {}
        for line in stock_moves:
            team_name = 'No_Name'
            if line.sale_id and line.sale_id.team_id:
                team_name = line.sale_id.team_id.name.replace(" ","_")
            
            if team_name in sm:
                sm[team_name].append(line)
            else:
                sm.update({team_name:[line]})
        
        #_logger.info("\nFinal : %s\n"%(sm))
        
        return {
            'doc_ids': stock_moves.ids,
            'doc_model': 'stock.move',
            'data': data['form'] if not docids else data,
            'docs': stock_moves,
            'sm':sm,
            'date_from':date_from.strftime("%m/%d/%y") if date_from else False,
            'date_to':date_to.strftime("%m/%d/%y") if date_to else False,
        }