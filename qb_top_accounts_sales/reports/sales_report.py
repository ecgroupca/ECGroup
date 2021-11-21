# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class TopAccountsReport(models.AbstractModel):

    _name = 'report.qb_top_accounts_sales.report_top_accounts_sales'
    _description = 'Top Accounts Sales Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        domain_search = []
        date_from = date_to = fields.Date.today()
        group_showrooms = data['form'].get('group_showrooms',False)
        partner_obj = self.env['res.partner']
        showroom_obj = self.env['crm.team']        
        where_clause = ' WHERE' 
        showrooms = {}
        partners = partner_obj
        top_clients = data['form'].get('top_clients',False)
        company_id = data['form'].get('company_id', False)
        company_id = company_id and company_id[0] or None  
        if company_id:
            where_clause += " SO.COMPANY_ID ='%s' AND"%(company_id)
        date_from = fields.Date.from_string(data['form'].get('date_from'))
        date_to = fields.Date.from_string(data['form'].get('date_to'))
        if date_from and date_to:
            if date_to < date_from:
                raise UserError(_('Your date from is greater than date to.')) 
            where_clause += " SO.DATE_ORDER >= '%s' AND SO.DATE_ORDER <= '%s' AND"%(date_from,date_to) 
            #domain_search += [('date_order','>=',date_from),('date_order','<=',date_to)]            
        if group_showrooms:                
            query = """SELECT SUM(SO.AMOUNT_TOTAL),SO.TEAM_ID,P.ID FROM SALE_ORDER SO 
                LEFT JOIN RES_PARTNER P ON P.ID = SO.PARTNER_ID
                LEFT JOIN CRM_TEAM CT ON CT.ID = SO.TEAM_ID
                %s
                SO.STATE IN ('done','sale')
                AND SO.AMOUNT_TOTAL > 0
                AND CT.ACTIVE = 't'
                GROUP BY SO.TEAM_ID,P.ID ORDER BY 1 DESC
                """%(where_clause)
            self.env.cr.execute(query)
            sm_client_sums = self.env.cr.fetchall()
            for client in sm_client_sums:
                team_name = 'No_Name'
                if client[1]:
                    partner = partner_obj.browse(client[2])
                    partners += partner 
                    team = showroom_obj.browse(client[1])
                    team_name = team.name.replace(" ","_")                 
                if team_name in showrooms and len(showrooms[team_name]) < top_clients:
                    showrooms[team_name].append(partner)
                elif team_name not in showrooms:
                    showrooms.update({team_name:[partner]}) 
        else:
            query = """SELECT SUM(SO.AMOUNT_TOTAL),P.ID FROM SALE_ORDER SO 
                LEFT JOIN RES_PARTNER P ON P.ID = SO.PARTNER_ID
                %s
                SO.STATE IN ('done','sale')
                AND SO.AMOUNT_TOTAL > 0
                GROUP BY P.ID ORDER BY 1 DESC
                """%(where_clause)
            self.env.cr.execute(query)
            client_sums = self.env.cr.fetchall() 
            for client in client_sums:
                if len(partners) >= top_clients:
                    break
                partner = partner_obj.browse(client[1])
                partners += partner   
                #team_name = ''               
                #if team_name in showrooms and len(showrooms[team_name]) < top_clients:
                #    showrooms[team_name].append(partner)
                #elif team_name not in showrooms:
                #    showrooms.update({team_name:[partner]})                 
          
        return {
            'doc_ids': partners.ids,
            'doc_model': 'res.partner',
            'data': data['form'] if not partners else data,
            'docs': partners,
            'sm':showrooms,
            'group_showrooms':group_showrooms,
            'date_from':date_from.strftime("%m-%d-%Y") if date_from else False,
            'date_to':date_to.strftime("%m-%d-%Y") if date_to else False,
        }