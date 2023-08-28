# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

WIP Report:
i.	1.Planned Date - Change to Order Date [DONE]
2. Add in Deadline Date
3. Remove Reserved column
4. Remove Status column
5. Add in Client Name



class WIPReportXlsx(models.AbstractModel):

    _name = 'report.qb_wip_report.wip_report_xlsx'
    _description = 'WIP Report Xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    
    def generate_xlsx_report(self, workbook, data, report):
        domain_search = []
        mrp_wo_obj = self.env['mrp.workorder']       
        workcenter_ids = data['form'].get('workcenter_id', False)
        user_id = data['form'].get('user_id', False)
        company_id = data['form'].get('company_id', False)
        domain = [('state','not in',['done','cancel'])]
        domain += [('production_id.state','not in',['draft','cancel','done','confirmed'])] 
        domain += [('company_id','=',company_id[0])]        
        if workcenter_ids:
            domain.append(('workcenter_id','in',workcenter_ids))
        if user_id:
            domain.append(('production_id.user_id','=',user_id[0]))
        sheet = workbook.add_worksheet('WIP Report')
        bold = workbook.add_format({'bold': True})
        sheet.write(0, 1, 'WIP Report', bold)
        work_orders = mrp_wo_obj.search(domain,order="production_id")  
        if len(work_orders) == 0:
            raise UserError(_('No workorders found.'))         
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
            sheet.write(i+j+5, 1, 'Order Date', bold)
            sheet.write(i+j+5, 2, 'Deadline', bold)            
            sheet.write(i+j+5, 3, 'Item#', bold)
            sheet.write(i+j+5, 4, 'Product', bold)
            sheet.write(i+j+5, 5, 'Sale', bold)
            sheet.write(i+j+5, 6, 'Client', bold)
            sheet.write(i+j+5, 7, 'Qty', bold)
            sheet.write(i+j+5, 8, 'Next Workorder', bold)
            sheet.write(i+j+5, 9, 'Responsible', bold)
            sheet.write(i+j+5, 10, 'Notes', bold)
            
            for wo in workcenters[sroom]: 
                i+=1   
                sale_id = wo.production_id.sale_order_id
                sale_name = sale_id and sale_id.name or ''
                client_name = sale_id.partner_id and sale_id.partner_id.name or ''
                date_order = sale_id and sale_id.date_order and date_order.strftime("%m-%d-%Y") or ''
                next_wo_id = wo.next_wo_id
                next_wo_name = next_wo_id and next_wo_id.name or ''
                user_id = wo.production_id.user_id
                resp_name = user_id and user_id.name or ''                
                sheet.write(j+i+5, 0, wo.production_id.name)                
                sheet.write(j+i+5, 1, date_order)
                sheet.write(j+i+5, 2, wo.production_id.date_deadline.strftime("%m-%d-%Y"))
                sheet.write(j+i+5, 3, wo.production_id.product_id.default_code or '')
                sheet.write(j+i+5, 4, wo.production_id.product_id.name or '')               
                sheet.write(j+i+5, 5, sale_name)
                sheet.write(j+i+5, 6, client_name)
                sheet.write(j+i+5, 7, wo.production_id.product_qty)
                sheet.write(j+i+5, 8, next_wo_name)
                sheet.write(j+i+5, 9, resp_name)
                sheet.write(j+i+5, 10, wo.production_id.x_notes)
                i+=1
                

class ReportWIPReport(models.AbstractModel):
    _name = 'report.qb_wip_report.report_wip'
    _description = 'WIP Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        domain = []
        mrp_wo_obj = self.env['mrp.workorder']       
        if not docids:
            company_id = data['form'].get('company_id', False)
            workcenter_ids = data['form'].get('workcenter_id', False)
            user_id = data['form'].get('user_id', False)
            domain = [('state','not in',['done','cancel']),('production_id.state','not in',['draft','cancel','done','confirmed'])] 
            domain += [('company_id','=',company_id[0])]           
            if workcenter_ids:
                domain.append(('workcenter_id','in',workcenter_ids))
            if user_id:
                domain.append(('production_id.user_id','=',user_id[0]))
        else:
            domain = [('id','in',docids)]  
        work_orders = mrp_wo_obj.search(domain,order="production_id") 
        if len(work_orders) == 0:
            raise UserError(_('No workorders found.'))         
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