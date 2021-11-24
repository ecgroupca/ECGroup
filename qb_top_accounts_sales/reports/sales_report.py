# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
import io
import base64

class TopAccountsXlsx(models.AbstractModel):

    _name = 'report.qb_top_accounts_sales.report_top_accounts_xlsx'
    _description = 'Top Sales Accounts Report Xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    
    def generate_xlsx_report(self, workbook, data, report):
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
        date_from = fields.Datetime.from_string(data['form'].get('date_from'))
        date_to = fields.Datetime.from_string(data['form'].get('date_to'))       
        if date_from and date_to:
            date_from_display = date_from.strftime("%m-%d-%Y")
            date_to_display = date_to.strftime("%m-%d-%Y")
            if date_to < date_from:
                raise UserError(_('Your date from is greater than date to.')) 
            where_clause += " SO.DATE_ORDER >= '%s' AND SO.DATE_ORDER <= '%s' AND"%(date_from,date_to) 
        sheet = workbook.add_worksheet('Top Sales Accounts')
        bold = workbook.add_format({'bold': True})
        title = workbook.add_format({'bold': True,'font_size': 20})
        i,j = 0,0 
        if company_id:
            logo = self.env['res.company'].browse(company_id).logo
            logo = io.BytesIO(base64.b64decode(logo))
            sheet.insert_image('A1', "logo.png", {'image_data': logo,}) 
            j = 1           
        sheet.write(8, 1, 'Top Sales Accounts', title)   
        if date_to and date_from:
            sheet.write(9, j, 'Date From: ' + date_from_display, bold)      
            sheet.write(9, j+3, 'Date To: ' + date_to_display, bold)       
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
                team_id = 0
                if client[1]:
                    partner = partner_obj.browse(client[2])
                    partners += partner
                    team_id = client[1]                
                if team_id in showrooms and len(showrooms[team_id]) < top_clients:
                    showrooms[team_id].append(partner)
                elif team_id not in showrooms:
                    showrooms.update({team_id:[partner]}) 
            for team_id in showrooms.keys():
                j+=2               
                showroom = showroom_obj.browse(team_id) or 'Not found'            
                sheet.write(i+j+7, 1, 'Showroom: ' + showroom.name, bold)
                sheet.write(i+j+8, 0, 'Client', bold)
                sheet.write(i+j+8, 1, 'Total', bold)
                sheet.write(i+j+8, 2, 'Street', bold)
                sheet.write(i+j+8, 3, 'Street 2', bold)
                sheet.write(i+j+8, 4, 'City', bold)
                sheet.write(i+j+8, 5, 'State', bold)
                sheet.write(i+j+8, 6, 'Zip Code', bold)
                sheet.write(i+j+8, 7, 'Country', bold)
                
                for cust in showrooms[team_id]: 
                    i+=1  
                    amount_total = 0.00
                    for sale in cust.sale_order_ids:
                        conditions = sale.state in ['sale','done'] and sale.team_id == showroom
                        if company_id:
                            conditions = conditions and sale.company_id.id == company_id
                        if date_from and date_to:
                            conditions = conditions and sale.date_order <= date_to and sale.date_order >= date_from
                        if conditions:
                            amount_total += sale.amount_total             
                    sheet.write(j+i+8, 0, cust.name or '', bold)
                    sheet.write(j+i+8, 1, "% 12.2f" %amount_total)
                    sheet.write(j+i+8, 2, cust.street or '')
                    sheet.write(j+i+8, 3, cust.street2 or '')
                    sheet.write(j+i+8, 4, cust.city or '')
                    sheet.write(j+i+8, 5, cust.state_id and cust.state_id.name or '')
                    sheet.write(j+i+8, 6, cust.zip or '')
                    sheet.write(j+i+8, 7, cust.country_id and cust.country_id.name or '')
                    i+=1
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
            sheet.write(i+j+9, 0, 'Client', bold)
            sheet.write(i+j+9, 1, 'Total', bold)
            sheet.write(i+j+9, 2, 'Street', bold)
            sheet.write(i+j+9, 3, 'Street 2', bold)
            sheet.write(i+j+9, 4, 'City', bold)
            sheet.write(i+j+9, 5, 'State', bold)
            sheet.write(i+j+9, 6, 'Zip Code', bold)
            sheet.write(i+j+9, 7, 'Country', bold)           
            for client in client_sums:
                if len(partners) >= top_clients:
                    break
                partner = partner_obj.browse(client[1])
                #partners += partner                                          
                i+=1  
                amount_total = 0.00
                for sale in partner.sale_order_ids:
                    conditions = sale.state in ['sale','done']
                    if company_id:
                        conditions = conditions and sale.company_id.id == company_id
                    if date_from and date_to:
                        conditions = conditions and sale.date_order <= date_to and sale.date_order >= date_from
                    if conditions:
                        amount_total += sale.amount_total             
                sheet.write(j+i+9, 0, partner.name or '', bold)
                sheet.write(j+i+9, 1, "% 12.2f" %amount_total)
                sheet.write(j+i+9, 2, partner.street or '')
                sheet.write(j+i+9, 3, partner.street2 or '')
                sheet.write(j+i+9, 4, partner.city or '')
                sheet.write(j+i+9, 5, partner.state_id and partner.state_id.name or '')
                sheet.write(j+i+9, 6, partner.zip or '')
                sheet.write(j+i+9, 7, partner.country_id and partner.country_id.name or '')
                i+=1

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