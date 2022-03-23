# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ItemDetailsXlsx(models.AbstractModel):

    _name = 'report.qb_itemdetails_reports.report_itemdetails_xlsx'
    _description = 'Item Details Report Xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    
    def generate_xlsx_report(self, workbook, data, report):
        domain_search = []
        prod_obj = self.env['product.product']        
        company_id = data['form'].get('company_id', False)
        company_id = company_id and company_id[0] or None
        domain_search = [('company_id','=',company_id)] 
        category_ids = data['form'].get('category_ids', False)
        domain_search = []
        if category_ids:        
            domain_search = [('categ_id','in',category_ids)]    
        products = prod_obj.search(domain_search)      
        product_groups = {}
        sheet = workbook.add_worksheet('Item Details')
        bold = workbook.add_format({'bold': True})
        sheet.write(0, 1, 'Item Details Report', bold)
        i,j = 0,0
        for prod in products:
            cat_name = 'No_Name'
            if prod.categ_id:
                cat_name = prod.categ_id.name.replace(" ","_")           
            if cat_name in product_groups:
                product_groups[cat_name].append(prod)
            else:
                product_groups.update({cat_name:[prod]})
                
        for prod_cat in product_groups.keys():
            j+=2       
            sheet.write(i+j+4, 1, 'Category: ' + prod_cat, bold)
            sheet.write(i+j+5, 0, 'Item Code', bold)
            sheet.write(i+j+5, 1, 'Quantity on Hand', bold)
            sheet.write(i+j+5, 2, 'Qty Forecasted', bold)
            sheet.write(i+j+5, 3, 'Qty Reserved', bold)
            sheet.write(i+j+5, 4, 'Reserved Order', bold)
            sheet.write(i+j+5, 5, 'Reserved Lot', bold)
            sheet.write(i+j+5, 6, 'Reserved Qty', bold)
            
            for prod in product_groups[prod_cat]: 
                
                i+=1 
                order_names = ''
                res_qty = 0
                for order in prod.reserved_order_ids:
                    if order and order.name:
                        order_names += str(order and order.name or '') + ','
                        res_qty += order.product_uom_qty
                order_names = order_names and order_names[:-1] or ''                    
                sheet.write(j+i+5, 0, prod.default_code or '', bold)
                sheet.write(j+i+5, 1, prod.qty_available)
                sheet.write(j+i+5, 2, prod.virtual_available)
                sheet.write(j+i+5, 3, res_qty)
                #loops through all reserved orders to print the reservation 
                #details in the last 3 columns
                for res_order in prod.reserved_order_ids:
                    if res_order and res_order.name:
                        sheet.write(j+i+5, 4, res_order.name)
                        sheet.write(j+i+5, 5, res_order.move_line_id and\
                        res_order.move_line_id.lot_id and\
                        res_order.move_line_id.lot_id.name or '')
                        sheet.write(j+i+5, 6, res_order.product_uom_qty)
                        i+=1
                i+=1
            
class ItemDetailsReport(models.AbstractModel):

    _name = 'report.qb_itemdetails_reports.report_itemdetails'
    _description = 'Item Details Report'
            
    @api.model
    def _get_report_values(self, docids, data=None):
        domain_search = []
        prod_obj = self.env['product.product']        
        company_id = data['form'].get('company_id', False)
        company_id = company_id and company_id[0] or None
        domain_search = [('company_id','=',company_id)] 
        category_ids = data['form'].get('category_ids', False)        
        if category_ids:        
            domain_search.append(('categ_id','in',category_ids))   
        products = prod_obj.search(domain_search)      
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
            'doc_model': 'product.product',
            'data': data['form'] if not docids else data,
            'docs': products,
            'cats':product_groups,
        }