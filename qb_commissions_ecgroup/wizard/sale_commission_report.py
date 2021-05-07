# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime

class ReportSaleCommissionReport(models.AbstractModel):

    _name = 'report.sale_mods_ecgroup.report_sale_commission'
    _description = 'Sale Commission report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = fields.Date.from_string(data['form'].get('date_from')) or fields.Date.today()
        date_to = fields.Date.from_string(data['form'].get('date_to')) or fields.Date.today()
        showroom = data['form'].get('showroom', False)
        
        domain_search = [('create_date','>=',date_from),('create_date','<=',date_to)]
        if showroom:
            domain_search.append(('team_id','in',showroom))
        sale_commissions = self.env['sale.commission'].search(domain_search)
        
        sale_comm = {}
        for commission in sale_commissions:
            customer_key = 'c_%s'%(commission.partner_id.id)
            team_name = 'No_Name'
            if commission.team_id:
                team_name = commission.team_id.name.replace(" ","_")
            
            if team_name in sale_comm:
                if customer_key in sale_comm[team_name]:
                    sale_comm[team_name][customer_key]['data'].append(commission)
                else:
                    sale_comm[team_name].update({customer_key:{'name':commission.partner_id.name,'ref':commission.partner_id.ref ,'id':commission.partner_id.id,'data':[commission]}})
            else:
                sale_comm.update({team_name:{customer_key:{'name':commission.partner_id.name,'ref':commission.partner_id.ref,'id':commission.partner_id.id,'data':[commission]}}})
        
        return {
            'doc_ids': sale_commissions.ids,
            'doc_model': 'sale.commission',
            'data': data['form'],
            'docs': sale_commissions,
            'sale_comm':sale_comm,
            'date_from':date_from.strftime("%d-%m-%Y"),
            'date_to':date_to.strftime("%d-%m-%Y"),
        }