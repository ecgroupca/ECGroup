# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

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
            domain = [('production_id.state','not in',['draft','cancel','done','confirmed'])]              
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