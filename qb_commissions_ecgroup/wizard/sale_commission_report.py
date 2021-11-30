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
        bold = workbook.add_format({'bold': True,'underline': 1})
        bold_cust = workbook.add_format({'bold': True,'font_size': 13})
        subtitle = workbook.add_format({'bold': True,'font_size': 15})
        title = workbook.add_format({'bold': True,'font_size': 20})
        if print_excel:
            for commission in comm_sales:
                if commission.team_id:
                    team_name = commission.team_id.name
                    team_id = commission.team_id.id
                if team_id not in sale_comm:
                    sale_comm.update({team_id:[commission]})
                else:
                    sale_comm[team_id].append(commission)  
                           
            for team_id in sale_comm.keys():                             
                showroom = showroom_obj.browse(team_id) or 'Not found'                        
                sheet = workbook.add_worksheet(showroom.name)            
                sheet.write(1, 2, showroom.name, title)
                sheet.write(3, 0, 'Order #', bold)
                sheet.write(3, 1, 'PO #', bold)
                sheet.write(3, 2, 'Client', bold)               
                sheet.write(3, 3, 'Rate', bold)
                #star goes in this column, no heading
                sheet.write(3, 5, 'Total Sale', bold)
                sheet.write(3, 6, 'Commission', bold)
                showroom_amt_total = 0.00
                showroom_comm_payable_total = 0.00
                place_star = False
                i=4
                for sale in sale_comm[team_id]:  
                    comm_rate = 0.00
                    comm_rate_product_count = 0
                    comm_subtotal = 0
                    for line in sale.order_line:
                        if not line.product_id.no_commissions: 
                            if line.product_id.type not in ['service','consu'] and line.comm_rate > 0.00:
                                comm_rate = comm_rate + line.comm_rate
                                comm_rate_product_count = comm_rate_product_count + 1 
                                comm_subtotal = comm_subtotal + line.comm_rate*line.price_subtotal/100                                
                                if comm_rate_product_count > 1:
                                    comm_rate = comm_rate/comm_rate_product_count
                    if comm_rate < 25.00:
                        place_star = True
                        
                    sheet.write(i, 0, sale.name or '', bold)              
                    sheet.write(i, 1, sale.client_order_ref or '')
                    sheet.write(i, 2, sale.partner_id.name or '')
                    sheet.write(i, 3, '$' + str("% 12.2f" %comm_rate))
                    sheet.write(i, 4, place_star and '*' or '')                   
                    sheet.write(i, 5, '$' + str("% 12.2f" %sale.amount_total))
                    sheet.write(i, 6, '$' + str("% 12.2f" %comm_subtotal))
                    i+=1
                    #calc showroom totals
                    showroom_amt_total += sale.amount_total
                    showroom_comm_payable_total += comm_subtotal
                sheet.write(i, 3, showroom.name + ' Total:',bold)
                sheet.write(i, 5, '$' + str("% 12.2f" %showroom_amt_total),bold)
                sheet.write(i, 6, '$' + str("% 12.2f" %showroom_comm_payable_total),bold)
                if place_star:
                    sheet.write(i+1, 2,'*Reduced Commission due to split or discount applied')

        else:
            for commission in comm_sales:
                customer_key = 'c_%s'%(commission.partner_id.id)
                if commission.team_id:
                    team_id = commission.team_id.id           
                if team_id in sale_comm:
                    if customer_key in sale_comm[team_id]:
                        sale_comm[team_id][customer_key]['data'].append(commission)
                    else:
                        sale_comm[team_id].update({customer_key:{'name':commission.partner_id.name,'ref':commission.partner_id.ref ,'id':commission.partner_id.id,'data':[commission]}})
                else:
                    sale_comm.update({team_id:{customer_key:{'name':commission.partner_id.name,'ref':commission.partner_id.ref,'id':commission.partner_id.id,'data':[commission]}}})     
            i,j = 0,0
            sheet = workbook.add_worksheet('Commission Report')
            sheet.write(1, 1, 'Sales Commission Report', title) 
            for showroom in sale_comm:
                j+=2               
                showroom_name = showroom_obj.browse(showroom)
                showroom_name = showroom_name and showroom_name.name or 'Not found'                
                sheet.write(i+j+1, 1, 'Showroom: ' + showroom_name, subtitle)
                sheet.write(i+j+2, 0, 'Order #', bold)
                sheet.write(i+j+2, 1, 'Invoice #', bold)
                sheet.write(i+j+2, 2, 'PO #', bold)
                sheet.write(i+j+2, 3, 'Inv Date', bold)
                sheet.write(i+j+2, 4, 'Comm', bold)
                sheet.write(i+j+2, 5, 'Inv Total', bold)
                sheet.write(i+j+2, 6, 'Sales Subject to Commission', bold)
                sheet.write(i+j+2, 7, 'Non-commission Amount', bold)
                sheet.write(i+j+2, 8, 'Inv Amount Paid', bold)
                sheet.write(i+j+2, 9, 'Commission Payable', bold)
                showroom_inv_total = 0.00
                showroom_sales_sub_to_commi_total = 0.00
                showroom_non_comm_amt_total = 0.00
                showroom_inv_amt_paid_total = 0.00 
                showroom_comm_payable_total = 0.00
                
                for cust in sale_comm.get(showroom):
                    sheet.write(i+j+3, 0, sale_comm[showroom][cust]['ref'] or '', bold_cust)
                    sheet.write(i+j+3, 1, sale_comm[showroom][cust]['name'] or 'No name', bold_cust)
                    inv_total = 0.00
                    sales_sub_to_commi_total = 0.00
                    non_comm_amt_total = 0.00
                    inv_amt_paid_total = 0.00
                    comm_payable_total = 0.00
                    is_previous = 's0'
                    
                    i+=1
                    for comm in sale_comm[showroom][cust]['data']:
                        if is_previous != comm.name:
                            is_previous = comm.name
                            inv_total += comm.amount_total
                            non_comm_amt = 0.00
                            comm_rate = 0.00
                            comm_subtotal = 0.00
                            comm_amt_total = 0.00
                            comm_rate_product_count = 0

                            for line in comm.order_line:
                                if line.product_id.no_commissions or line.product_id.type in ['service','consu']:
                                    non_comm_amt = non_comm_amt + line.price_subtotal
                                elif not line.product_id.no_commissions: 
                                    if line.product_id.type not in ['service','consu'] and line.comm_rate > 0.00:
                                        comm_rate = comm_rate + line.comm_rate
                                        comm_amt_total = comm_amt_total + line.price_subtotal
                                        comm_subtotal = comm_subtotal + line.comm_rate*line.price_subtotal/100
                                        comm_rate_product_count = comm_rate_product_count + 1 
                                         
                            if comm_rate_product_count > 1:
                                comm_rate = comm_rate/comm_rate_product_count
                            non_comm_amt_total = non_comm_amt_total + non_comm_amt
                            sales_sub_to_commi = comm_amt_total
                            sales_sub_to_commi_total = sales_sub_to_commi_total + sales_sub_to_commi
                            commi_payable = comm_subtotal
                            comm_payable_total = comm_payable_total + commi_payable
                            inv_amt_paid = 0.00
                            
                            if comm.comm_inv_id:
                                inv_amt_paid = comm.comm_inv_id.amount_total - comm.comm_inv_id.amount_residual
                            inv_amt_paid_total = inv_amt_paid_total + inv_amt_paid 	                                        
                        sheet.write(j+i+3, 0, comm.name or '')
                        sheet.write(j+i+3, 1, comm.comm_inv_id and comm.comm_inv_id.name or '')
                        sheet.write(j+i+3, 2, comm.client_order_ref or '')
                        sheet.write(j+i+3, 3, comm.comm_inv_id and comm.comm_inv_id.invoice_date or '')
                        sheet.write(j+i+3, 4, '$' + str('% 12.2f' %comm_rate) or 0)
                        sheet.write(j+i+3, 5, '$' + str('% 12.2f' %comm.amount_total))
                        sheet.write(j+i+3, 6, '$' + str('% 12.2f' %sales_sub_to_commi))
                        sheet.write(j+i+3, 7, '$' + str('% 12.2f' %non_comm_amt))
                        sheet.write(j+i+3, 8, '$' + str('% 12.2f' %inv_amt_paid))
                        sheet.write(j+i+3, 9, '$' + str('% 12.2f' %commi_payable))
                        i+=1
                       
                    #Customer totals
                    sheet.write(j+i+3, 1, "Customer \'" + str(sale_comm[showroom][cust]['name']) + "\' Totals:", bold)
                    sheet.write(j+i+3, 5, '$' + str('% 12.2f'%inv_total), bold)
                    sheet.write(j+i+3, 6, '$' + str('% 12.2f' %sales_sub_to_commi_total), bold)
                    sheet.write(j+i+3, 7, '$' + str('% 12.2f' %non_comm_amt_total), bold)
                    sheet.write(j+i+3, 8, '$' + str('% 12.2f' %inv_amt_paid_total), bold)
                    sheet.write(j+i+3, 9, '$' + str('% 12.2f' %comm_payable_total), bold)                       
                    showroom_inv_total += inv_total
                    showroom_sales_sub_to_commi_total = showroom_sales_sub_to_commi_total + sales_sub_to_commi_total
                    showroom_non_comm_amt_total = showroom_non_comm_amt_total + non_comm_amt_total
                    showroom_inv_amt_paid_total = showroom_inv_amt_paid_total + inv_amt_paid_total
                    showroom_comm_payable_total = showroom_comm_payable_total + comm_payable_total	
                i+=2                  
                sheet.write(j+i+3, 1, "Showroom \'"  + showroom_name + "\' Totals:", bold)
                sheet.write(j+i+3, 5, '$' + str('% 12.2f' %showroom_inv_total), bold)
                sheet.write(j+i+3, 6, '$' + str('% 12.2f' %showroom_sales_sub_to_commi_total), bold)
                sheet.write(j+i+3, 7, '$' + str('% 12.2f' %showroom_non_comm_amt_total), bold)
                sheet.write(j+i+3, 8, '$' + str('% 12.2f' %showroom_inv_amt_paid_total), bold)
                sheet.write(j+i+3, 9, '$' + str('% 12.2f' %showroom_comm_payable_total), bold)
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