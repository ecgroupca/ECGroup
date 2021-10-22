# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import api, fields, models, _
from datetime import datetime


class ReportIndepContractor(models.AbstractModel):

    _name = 'report.qb_indep_contractor.report_indep_contractor'
    _description = 'Independent Contractor Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = fields.Date.from_string(data['form'].get('date_from')) or fields.Date.today()
        date_to = fields.Date.from_string(data['form'].get('date_to')) or fields.Date.today()
        if date_to < date_from:
            raise UserError(_('Your date from is greater than date to.'))
        vendor_id = data['form'].get('vendor_id', False)
        #search on res.parter where id is the vendor_id 
        import pdb;pdb.set_trace()        
        domain_search = [('id','=',vendor_id),('create_date','>=',date_from),('create_date','<=',date_to)]
        indep_cons = self.env['res.partner'].search(domain_search)
        return {
            'doc_ids': indep_cons.ids,
            'doc_model': 'res.partner',
            'data': data['form'],
            'docs': indep_cons,
            'date_from':date_from.strftime("%m-%d-%Y"),
            'date_to':date_to.strftime("%m-%d-%Y"),
        }