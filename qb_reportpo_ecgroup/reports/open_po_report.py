# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

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
        po_ids = self.env['purchase.order'].search(domain_search,order="id desc")       
        sm = {}
        for po in po_ids:
            vendor_name = "%s_%s"%(po.partner_id.name.replace(" ","_"),po.partner_id.id)
            
            if vendor_name in sm:
                sm[vendor_name]['data'].append(po)
            else:
                sm.update({vendor_name:{'name':po.partner_id.name,'ref':po.partner_id.ref,'data':[po]}})
        
        #_logger.info("\nFinal : %s\n"%(sm))
        
        return {
            'doc_ids': po_ids.ids,
            'doc_model': 'purchase.order',
            'data': data['form'] if not docids else data,
            'docs': po_ids,
            'sm':sm,
            'date_from':date_from.strftime("%d-%m-%Y") if date_from else False,
            'date_to':date_to.strftime("%d-%m-%Y") if date_to else False,
        }