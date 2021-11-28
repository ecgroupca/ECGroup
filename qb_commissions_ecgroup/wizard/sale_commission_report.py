# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import api, fields, models, _
from datetime import datetime


class CommissionsReportXlsx(models.AbstractModel):

    _name = 'report.qb_commissions_ecgroup.report_sale_commission_xlsx'
    _description = 'Commissions Report Xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    
    def generate_xlsx_report(self, workbook, data, report):
        showroom_obj = self.env['crm.team']  
        print_excel = data['form'].get('print_excel',False)
        date_from = fields.Date.from_string(data['form'].get('date_from')) or fields.Date.today()
        date_to = fields.Date.from_string(data['form'].get('date_to')) or fields.Date.today()
        if date_to < date_from:
            raise UserError(_('Your date from is greater than date to.'))
        showroom = data['form'].get('showroom', False)
        remove_paid = data['form'].get('remove_paid', False)   
        #create the domain for sales eligible for commissions  
        #domain_search = [('inv_bal_due','<=',0),('open_shipment','=',False),('comm_total','>',0),('create_date','>=',date_from),('create_date','<=',date_to)]
        domain_search = [('comm_total','>',0)]
        if showroom:
            domain_search.append(('team_id','in',showroom)) 
        if remove_paid:
            domain_search.append(('comm_inv_paid','!=',True))  
        comm_sales = self.env['sale.order'].search(domain_search)             
        sale_comm = {}
        #Order #	P.O. # 	Client 			Total Sale	 Commission  
        bold = workbook.add_format({'bold': True})
        title = workbook.add_format({'bold': True,'font_size': 20})
        #import pdb;pdb.set_trace()
        if print_excel:
            for commission in comm_sales:
                if commission.team_id:
                    team_name = commission.team_id.name
                    team_id = commission.team_id.id
                if team_id not in sale_comm:
                    sale_comm.update({team_id:[commission]})
                else:
                    sale_comm[team_id].append(commission)  
                           
            for team_id in showrooms.keys():                             
                showroom = showroom_obj.browse(team_id) or 'Not found'                        
                sheet = workbook.add_worksheet(showroom.name)            
                sheet.write(1, 2, showroom.name, title)
                sheet.write(3, 0, 'Order #', bold)
                sheet.write(3, 1, 'PO #', bold)
                sheet.write(3, 2, 'Client', bold)
                sheet.write(3, 3, 'Total Sale', bold)
                sheet.write(3, 4, 'Commission', bold)
                i=4
                for sale in showrooms[team_id]:             
                    sheet.write(i, 0, sale.name or '', bold)              
                    sheet.write(i, 1, sale.client_order_ref or '')
                    sheet.write(i, 2, sale.partner_id.name or '')
                    sheet.write(i, 3, "% 12.2f" %sale.amount_total)
                    sheet.write(i, 4, sale.comm_total or '')
                    i+=1
        else:
            for commission in comm_sales:
                customer_key = 'c_%s'%(commission.partner_id.id)
                if commission.team_id:
                    team_id = commission.team_id.id           
                if team_id in showrooms:
                    if customer_key in showrooms[team_id]:
                        showrooms[team_id][customer_key]['data'].append(commission)
                    else:
                        showrooms[team_id].update({customer_key:{'name':commission.partner_id.name,'ref':commission.partner_id.ref ,'id':commission.partner_id.id,'data':[commission]}})
                else:
                    showrooms.update({team_id:{customer_key:{'name':commission.partner_id.name,'ref':commission.partner_id.ref,'id':commission.partner_id.id,'data':[commission]}}})     
            i,j = 0,0
            sheet = workbook.add_worksheet('Commission Report')
            sheet.write(8, 1, 'Sales Commission Report', title) 
            for team_id in showrooms.keys():
                j+=2               
                showroom = showroom_obj.browse(team_id) or 'Not found'   				
                import pdb;pdb.set_trace()                
                sheet.write(i+j+7, 1, 'Showroom: ' + showroom.name, bold)
                sheet.write(i+j+8, 0, 'Order #', bold)
                sheet.write(i+j+8, 1, 'Invoice #', bold)
                sheet.write(i+j+8, 2, 'PO #', bold)
                sheet.write(i+j+8, 3, 'Inv Date', bold)
                sheet.write(i+j+8, 4, 'Comm', bold)
                sheet.write(i+j+8, 5, 'Inv Total', bold)
                sheet.write(i+j+8, 6, 'Sales Subject to Commission', bold)
                sheet.write(i+j+8, 7, 'Non-commission Amount', bold)
                sheet.write(i+j+8, 8, 'Inv Amount Paid', bold)
                sheet.write(i+j+8, 9, 'Commission Payable', bold)
                showroom_inv_total = "0.00"
				showroom_sales_sub_to_commi_total = 0.00 
				showroom_non_comm_amt_total = 0.00
				showroom_inv_amt_paid_total = 0.00 
				showroom_comm_payable_total = 0.00
                inv_total = 0.00
				sales_sub_to_commi_total = 0.00
				non_comm_amt_total = 0.00
				inv_amt_paid_total = 0.00
				comm_payable_total = 0.00
                sheet.write(i+j+9, 1, sale_comm[showroom][cust]['ref'], bold)
                sheet.write(i+j+9, 3, sale_comm[showroom][cust]['name'], bold)	

				is_previous = s0
				for comm in sale_comm[showroom][cust]['data']:
					    				<t t-if="comm and is_previous != comm.name">
					    					<t t-set="is_previous" t-value="comm.name"/>
						    				
						    				<t t-set="inv_total" t-value="inv_total + comm.amount_total"/>
						    				
						    				<t t-set="non_comm_amt" t-value="0.00"/>
						    				<t t-set="comm_rate" t-value="0.00"/>
											<t t-set="comm_subtotal" t-value="0.00"/>
											<t t-set="comm_amt_total" t-value="0.00"/>
						    				<t t-set="comm_rate_product_count" t-value="0"/>                
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
                    

class ReportSaleCommissionReport(models.AbstractModel):

    _name = 'report.qb_commissions_ecgroup.report_sale_commission'
    _description = 'Sale Commission report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = fields.Date.from_string(data['form'].get('date_from')) or fields.Date.today()
        date_to = fields.Date.from_string(data['form'].get('date_to')) or fields.Date.today()
        if date_to < date_from:
            raise UserError(_('Your date from is greater than date to.'))
        showroom = data['form'].get('showroom', False)
        remove_paid = data['form'].get('remove_paid', False)   
        #create the domain for sales eligible for commissions  
        domain_search = [('inv_bal_due','<=',0),('open_shipment','=',False),('comm_total','>',0),('create_date','>=',date_from),('create_date','<=',date_to)]
        if showroom:
            domain_search.append(('team_id','in',showroom)) 
        if remove_paid:
            domain_search.append(('comm_inv_paid','!=',True))  
        comm_sales = self.env['sale.order'].search(domain_search)             
        sale_comm = {}
        for commission in comm_sales:
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
            'doc_ids': comm_sales.ids,
            'doc_model': 'sale.order',
            'data': data['form'],
            'docs': comm_sales,
            'sale_comm':sale_comm,
            'date_from':date_from.strftime("%m-%d-%Y"),
            'date_to':date_to.strftime("%m-%d-%Y"),
        }