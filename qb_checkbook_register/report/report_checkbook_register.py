# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

          
class CheckbookRegisterReport(models.AbstractModel):

    _name = 'report.qb_checkbook_register.report_checkbook_reg'
    _description = 'Checkbook Register Report'
            
    @api.model
    def _get_report_values(self, docids, data=None):
        domain_search = []
        date_from = date_to = fields.Date.today()
        check_obj = self.env['account.payment']             
        date_from = fields.Date.from_string(data['form'].get('date_from')) or fields.Date.today()
        date_to = fields.Date.from_string(data['form'].get('date_to')) or fields.Date.today()
        if date_from and date_to:
            date_from_display = date_from.strftime("%m-%d-%Y")
            date_to_display = date_to.strftime("%m-%d-%Y")
            if date_to < date_from:
                raise UserError(_('Your date from is greater than date to.')) 
        company_id = data['form'].get('company_id', False)
        company_id = company_id and company_id[0] or None
        date_domain = [('company_id','=',company_id)]
        date_domain += [('payment_date','>=',date_from.strftime("%Y-%m-%d 00:00:00"))]
        date_domain += [('payment_date','<=',date_to.strftime("%Y-%m-%d 23:59:59"))]
        date_domain += [('state','not in',['draft','sent','cancelled'])]
        date_domain += [('payment_method_id.name','=','Checks')]
        checks = check_obj.search(date_domain)                     
        return {
            'doc_ids': checks.ids,
            'doc_model': 'account.payment',
            'data': data['form'],
            'docs': checks,
            'date_from':date_from.strftime("%m-%d-%Y") if date_from else False,
            'date_to':date_to.strftime("%m-%d-%Y") if date_to else False,
        }