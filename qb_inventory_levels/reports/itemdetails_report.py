# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class InventoryLevelsXlsx(models.AbstractModel):

    _name = 'report.qb_inventory_levels.report_inventory_levels_xlsx'
    _description = 'Inventory Levels Report Xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    
    def generate_xlsx_report(self, workbook, data, report):
        domain_search = []
        one_year_ago = (datetime.now()-relativedelta(years=1))
        quant = self.env['stock.quant']        
        category_ids = data['form'].get('category_ids', False) 
        company_ids = self.env['res.company'].search([])
        for company_id in company_ids:
            loc_dom = [('usage','=','internal')]
            loc_dom += [('name','in',['Raw','Finished'])]
            loc_dom += [('company_id','in',[False, company_id.id])]
            internal_loc_ids = self.env['stock.location'].search(loc_dom)
            for internal_loc_id in internal_loc_ids:
                quants = internal_loc_id.quant_ids 
                if category_ids:             
                    quant_ids.filtered(lambda quant: quant.product_id.categ_id in category_ids)             
                product_groups = {}
                sheet = workbook.add_worksheet('%s'%internal_loc_id.name)
                bold = workbook.add_format({'bold': True})
                sheet.write(0, 1, 'Reordering Report for %s location'%internal_loc_id.name, bold)
                i,j = 0,0
                
                for quant_id in quants:
                
                    cat_name = 'No_Name'
                    product_id = quant_id.product_id
                    categ_id = product_id.categ_id
                    
                    if categ_id:
                        cat_name = categ_id.name.replace(" ","_")           
                    if cat_name in product_groups:
                        product_groups[cat_name].append(product_id)
                    else:
                        product_groups.update({cat_name:[product_id]})
                        
                for prod_cat in product_groups.keys():
                    j+=2       
                    sheet.write(i+j+4, 1, 'Category: ' + prod_cat, bold)
                    sheet.write(i+j+5, 0, 'Item', bold)
                    sheet.write(i+j+5, 1, 'Quantity on Hand', bold)
                    sheet.write(i+j+5, 2, 'Qty Forecasted', bold)
                    sheet.write(i+j+5, 3, 'Qty Reserved', bold)
                    sheet.write(i+j+5, 4, 'Qty Ordered', bold)
                    sheet.write(i+j+5, 5, 'Orders', bold)
                    
                    for prod in product_groups[prod_cat]: 
                        
                        i+=1 
                        order_names = ''
                        res_qty = 0
                        for order in prod.reserved_order_ids:
                            if order and order.name:
                                order_names += str(order and order.name or '') + ','
                                res_qty += order.product_uom_qty
                        order_names = order_names and order_names[:-1] or ''                    
                        sheet.write(j+i+5, 0, prod.display_name, bold)
                        sheet.write(j+i+5, 1, prod.qty_available)
                        sheet.write(j+i+5, 2, prod.virtual_available)
                        sheet.write(j+i+5, 3, res_qty)
                                
                        #search for all sale.order.line objects with the product for the past 365 days
                        domain = [('product_id','=',prod.id),('order_id.state','in',['purchase','to approve','sent'])]
                        purchase_lines = self.env['purchase.order.line'].search(domain)
                        qty_ordered = 0
                        qty_delivered = 0
                        order_numbers = ''
                        for line in purchase_lines:
                            qty_ordered += line.product_uom_qty
                            order_numbers += line.order_id.name
                        sheet.write(j+i+5, 4, qty_ordered)
                        orders = ', '.join(order_numbers)
                        sheet.write(j+i+5, 4, orders)
                        i+=1
                       
            
class ItemDetailsReport(models.AbstractModel):

    _name = 'report.qb_inventory_reports.report_inventory_levels'
    _description = 'Inventory Levels Report'
            
    @api.model
    def _get_report_values(self, docids, data=None):
        domain_search = []
        one_year_ago = (datetime.now()-relativedelta(years=1))
        quant = self.env['stock.quant']        
        company_id = data['form'].get('company_id', False)
        company_id = company_id and company_id[0] or None
        domain_search = [('company_id','=',company_id)] 
        category_ids = data['form'].get('category_ids', False)        
        if category_ids:        
            domain_search.append(('categ_id','in',category_ids))   
        products = quant.search(domain_search)      
        product_groups = {}
        for prod in products:
            cat_name = 'No_Name'
            if prod.categ_id:
                cat_name = prod.categ_id.name.replace(" ","_")           
            if cat_name in product_groups:
                product_groups[cat_name].append(prod)
            else:
                product_groups.update({cat_name:[prod]})
                
        return {
            'doc_ids': products.ids,
            'doc_model': 'stock.quant',
            'data': data['form'] if not docids else data,
            'docs': products,
            'cats': product_groups,
            'one_year_ago': one_year_ago,
        }