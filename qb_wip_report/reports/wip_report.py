# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class WIPReportXlsx(models.AbstractModel):

    _name = 'report.qb_wip_report.wip_report_xlsx'
    _description = 'WIP Report Xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    
    def generate_xlsx_report(self, workbook, data, report):
        domain_search = []
        mrp_wo_obj = self.env['mrp.workorder']       
        workcenter_ids = data['form'].get('workcenter_id', False)
        user_id = data['form'].get('user_id', False)
        domain = [('state','not in',['done','cancel']),('production_id.state','not in',['draft','cancel','done','confirmed'])]              
        if workcenter_ids:
            domain.append(('workcenter_id','in',workcenter_ids))
        if user_id:
            domain.append(('production_id.user_id','=',user_id[0]))
        sheet = workbook.add_worksheet('WIP Report')
        bold = workbook.add_format({'bold': True})
        sheet.write(0, 1, 'WIP Report', bold)
        work_orders = mrp_wo_obj.search(domain)         
        workcenters = {}
        for wo in work_orders:
            wc_name = wo.workcenter_id.name.replace(" ","_")           
            if wc_name in workcenters:
                workcenters[wc_name].append(wo)
            else:
                workcenters.update({wc_name:[wo]})   
        i,j = 0,-2
        for sroom in workcenters.keys(): 
            j+=2        
            sheet.write(i+j+4, 1, 'Workcenter: ', bold)
            sheet.write(i+j+4, 2, sroom, bold)
            sheet.write(i+j+5, 0, 'MO', bold)
            sheet.write(i+j+5, 1, 'Workorder', bold)
            sheet.write(i+j+5, 2, 'Date Planned', bold)
            sheet.write(i+j+5, 3, 'Product', bold)
            sheet.write(i+j+5, 4, 'Sale', bold)
            sheet.write(i+j+5, 5, 'Routing', bold)
            sheet.write(i+j+5, 6, 'Reserved', bold)
            sheet.write(i+j+5, 7, 'Qty', bold)
            sheet.write(i+j+5, 8, 'Status', bold)
            sheet.write(i+j+5, 9, 'Company', bold)
            sheet.write(i+j+5, 10, 'Next Workorder', bold)
            sheet.write(i+j+5, 11, 'Responsible', bold)
            
            for wo in workcenters[sroom]: 
                i+=1   
                sale_id = wo.production_id.sale_order_id
                sale_name = sale_id and sale_id.name or ''
                next_wo_id = wo.next_wo_id
                next_wo_name = next_wo_id and next_wo_id.name or ''
                user_id = wo.production_id.user_id
                resp_name = user_id and user_id.name or ''                
                sheet.write(j+i+5, 0, wo.production_id.name)                
                sheet.write(j+i+5, 1, wo.name)
                sheet.write(j+i+5, 2, wo.production_id.date_planned_start.strftime("%m-%d-%Y"))
                sheet.write(j+i+5, 3, wo.production_id.product_id.name or '')
                sheet.write(j+i+5, 4, sale_name)
                sheet.write(j+i+5, 5, wo.production_id.routing_id.name)
                sheet.write(j+i+5, 6, wo.production_id.reservation_state)
                sheet.write(j+i+5, 7, wo.production_id.product_qty)
                sheet.write(j+i+5, 8, wo.production_id.state)
                sheet.write(j+i+5, 9, wo.production_id.company_id.name)
                sheet.write(j+i+5, 10, next_wo_name)
                sheet.write(j+i+5, 11, resp_name)
                i+=1
                

class ReportWIPReport(models.AbstractModel):
    _name = 'report.qb_wip_report.report_wip'
    _description = 'WIP Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        domain_search = []
        mrp_wo_obj = self.env['mrp.workorder']       
        if not docids:
            
            workcenter_ids = data['form'].get('workcenter_id', False)
            user_id = data['form'].get('user_id', False)
            domain = [('state','not in',['done','cancel']),('production_id.state','not in',['draft','cancel','done','confirmed'])]              
            if workcenter_ids:
                domain.append(('workcenter_id','in',workcenter_ids))
            if user_id:
                domain.append(('production_id.user_id','=',user_id[0]))
        else:
            domain = [('id','in',docids)]       

        work_orders = mrp_wo_obj.search(domain)         
        workcenters = {}
        for wo in work_orders:
            wc_name = wo.workcenter_id.name.replace(" ","_")           
            if wc_name in workcenters:
                workcenters[wc_name].append(wo)
            else:
                workcenters.update({wc_name:[wo]})      
        
        return {
            'doc_ids': work_orders.ids,
            'doc_model': 'mrp.production',
            'data': data['form'] if not docids else data,
            'docs': work_orders,
            'user_id': user_id,
            'wc':workcenters,
        }