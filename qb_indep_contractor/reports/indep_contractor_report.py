# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import api, fields, models, _
from datetime import datetime


class ReportIndepContractor(models.AbstractModel):

    _name = 'report.qb_indep_contractor.report_indep_contractor'
    _description = 'Independent Contractor Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        #search on res.parter where id is the vendor_id      
        domain_search = [('id','in',docids),('needs_ten_ninety_nine','=',True)]      
        indep_cons = self.env['res.partner'].search(domain_search)
        return {
            'doc_ids': indep_cons.ids,
            'doc_model': 'res.partner',
            'data': data,
            'docs': indep_cons,
        }