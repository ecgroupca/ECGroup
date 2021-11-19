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
        partner_obj = self.env['res.partner'] 
        showroom_obj = self.env['crm.team']        
        where_clause = ' WHERE'        
        if not docids:
            date_from = fields.Date.from_string(data['form'].get('date_from'))
            date_to = fields.Date.from_string(data['form'].get('date_to'))
            if date_from and date_to:
                where_clause += " SO.DATE_ORDER >= '%s' AND SO.DATE_ORDER <= '%s' AND"%(date_from,date_to)
            top_clients = data['form'].get('top_clients',False)
            #num_showrooms = self.env['crm.team'].search([])
            #top_clients = top_clients*len(num_show_rooms)
            company_id = data['form'].get('company_id', False)
            company_id = company_id and company_id[0] or None  
            if company_id:
                where_clause += " SO.COMPANY_ID ='%s' AND"%(company_id)
                    
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
            #domain += [('invoice_status','=','to invoice'),('trans_shipped_date','!=',False)]
            #self.env.cr.execute("SELECT * FROM res_partner")
            #self.env.cr.fetchall()
            #if date_from and date_to:
            #    domain.append(('date_order','>=',date_from.strftime("%Y-%m-%d 00:00:00")))
            #    domain.append(('date_order','<=',date_to.strftime("%Y-%m-%d 23:59:59")))
            #sales_from_to = sale_obj.search(domain)
            #if showroom:
            #    domain.append(('team_id','in',showroom))
        else :
            date_from = date_to = False
            domain = [('id','in',docids)]
        #sale_orders = sale_obj.search(domain)  
        #partners = partner_obj        
        #for cli in clients:
        #    account = partner_obj.browse(cli[1])
        #    partners.append(account)       
        showrooms = {}
        partners = partner_obj
        for client in sm_client_sums:
            team_name = 'No_Name'
            #import pdb;pdb.set_trace()
            partner = partner_obj.browse(client[2])
            partners += partner
            if client[1]:
                team = showroom_obj.browse(client[1])
                team_name = team.name.replace(" ","_")                 
            if team_name in showrooms and len(showrooms[team_name]) < top_clients:
                showrooms[team_name].append(partner)
            elif team_name not in showrooms:
                showrooms.update({team_name:[partner]})           
        return {
            'doc_ids': partners.ids,
            'doc_model': 'res.partner',
            'data': data['form'] if not docids else data,
            'docs': partners,
            'sm':showrooms,
            'date_from':date_from.strftime("%m-%d-%Y") if date_from else False,
            'date_to':date_to.strftime("%m-%d-%Y") if date_to else False,
        }