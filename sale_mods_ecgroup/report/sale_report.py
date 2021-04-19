# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import models, fields, api
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
        

class CRMTeam(models.Model):
    _inherit = 'crm.team'
    
    default_comm_rate = fields.Float(
        'Default Commission Rate (%)', 
        readonly = False,
        stored = True,
    )
        
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    comments = fields.Char(
        'Comments'
    )
    no_commissions = fields.Boolean(
        'No Commissions',
    )
    
    @api.model
    def name_get(self):
        res = []
        product_name = ''
        for rec in self:
            name = rec.description and '\n'.join(rec.description.split('\n', 2)[:2]) or rec.name
            if name:
                if rec.default_code:
                    product_name = '[' + rec.default_code + '] ' + name
                else:
                    product_name = name
            elif rec.default_code:
                product_name = '[' + rec.default_code + ']'  
            else:
                product_name = name                     
            res.append((rec.id, "%s" % product_name))
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    @api.model
    def name_get(self):
        res = []
        product_name = ''
        for rec in self:
            name = rec.description and '\n'.join(rec.description.split('\n', 2)[:2]) or rec.name
            if name:
                if rec.default_code:
                    product_name = '[' + rec.default_code + '] ' + name
                else:
                    product_name = name
            elif rec.default_code:
                product_name = '[' + rec.default_code + ']'  
            else:
                product_name = name                     
            res.append((rec.id, "%s" % product_name))
        return res
        

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    reseller_id = fields.Char(
        'Reseller ID'
    )
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    comm_rate = fields.Float(
        'Commission Rate', 
        readonly = False,        
    )
    internal_note = fields.Char(
        'Internal Note'
    )        
                
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    deposit_total = fields.Float(
        'Total Deposits', 
        compute="_compute_deps_total",
        store = True,
    )
    approx_lead_time = fields.Char(
        'Approximate Lead Time',
        store = True,
    )
    sidemark = fields.Char(
        'Sidemark',
        store = True,
    ) 
    shipper_phone = fields.Char(
        'Shipper Phone',
        store = True,
    ) 
    customer_note = fields.Char(
        'Customer Note',
        store = True,
    )
    ship_name = fields.Char(
        'Shipper Name',
        store = True,
    )     
    etwo_number = fields.Char(
        'E2 Doc#',
        store = True,
    )  
    sales_associate = fields.Char(
        'Sales Associate',
        store = True,
    ) 
    user_id = fields.Many2one(
        'res.users',
        'Responsible',
        store = True,
    )    
    comm_total = fields.Float(
        'Total Commisions', 
        compute="_compute_deps_total",
        store = True,
    )
    inv_bal_due = fields.Float(
        'Balance Due',
        compute="_compute_bal_due",
        store = True,
    )
    taxed_order = fields.Boolean(
        'Taxable', 
    )

    """@api.onchange('carrier_id')
    def _onchange_carrier(self):
        for sale in self:
            #1. get deliveries for this sale
            #2. set the carrier
            pickings = self.env['stock.picking'].search([('sale_id','=',sale.id)])            
            for pick in pickings:
                pick.carrier_id = sale.carrier_id
                
    @api.onchange('user_id')
    def _onchange_user_id(self):
        for sale in self:
            #1. when user changes, push this value to all deliveries as user_id 
            pickings = self.env['stock.picking'].search([('sale_id','=',sale.id)])            
            for pick in pickings:
                pick.user_id = sale.user_id
                
    @api.onchange('partner_shipping_id')
    def _onchange_shipping_id(self):
        for sale in self:
            #1. when user changes, push this value to all deliveries as user_id 
            pickings = self.env['stock.picking'].search([('sale_id','=',sale.id)])            
            for pick in pickings:
                pick.partner_id = sale.partner_shipping_id"""
                
    def action_update_bal_due(self):
        for sale in self:
            amt_res = 0.00
            amt_inv = 0.00
            for invoice in sale.invoice_ids:
                if invoice.state=='posted':
                    amt_res += invoice.amount_residual
                    amt_inv += invoice.amount_total
            amt_due = (sale.amount_total - amt_inv) + amt_res
            sale.inv_bal_due = amt_due 
            total_deps = 0
            deposit_invs = []
            company_id = sale.company_id and sale.company_id.id or 1
            config = self.env['ir.config_parameter']
            setting = config.search([('key','=','sale.default_deposit_product_id')])
            setting = setting and setting[0] or None
            dep_product = setting and setting.value or None
            if dep_product:            
                try:
                    dep_product = int(dep_product)                                 
                except UserError as error:
                    raise UserError(error)  
                sale_dep_lines = self.order_line.search([('product_id','=',dep_product),('order_id','=',sale.id)])
                for line in sale_dep_lines:
                    amt_inv = 0.00
                    amt_res = 0.00
                    #must find the invoice corresponding with the deposit and sum the amount - residual from the invoice.
                    for inv_line in line.invoice_lines:
                        invoice = inv_line.move_id
                        invoice_id = invoice.id
                        if invoice_id not in deposit_invs:
                            deposit_invs.append(invoice_id)
                            if invoice.state=='posted':
                                amt_res += invoice.amount_residual
                                amt_inv += invoice.amount_total
                                total_deps += (amt_inv - amt_res)                
                sale.deposit_total = total_deps           
              
    @api.onchange('team_id')
    def _onchange_sales_team(self):
        for sale in self:
            def_comm_rate = sale.team_id.default_comm_rate
            if def_comm_rate:
                for line in sale.order_line:
                    if line.product_id.type == 'product':
                        line.comm_rate = def_comm_rate
                
    @api.depends('order_line')
    def _compute_deps_total(self):
        for sale in self:
            amt_res = 0.00
            amt_inv = 0.00
            for invoice in sale.invoice_ids:
                if invoice.state=='posted':
                    amt_res += invoice.amount_residual
                    amt_inv += invoice.amount_total
            amt_due = (sale.amount_total - amt_inv) + amt_res
            sale.inv_bal_due = amt_due 
            total_deps = 0
            total_comm = 0
            company_id = sale.company_id and sale.company_id.id or 1
            config = self.env['ir.config_parameter']
            setting = config.search([('key','=','sale.default_deposit_product_id')])
            setting = setting and setting[0] or None
            dep_product = setting and setting.value or None
            if dep_product:            
                try:
                    dep_product = int(dep_product)                                 
                except UserError as error:
                    raise UserError(error)  
                sale_dep_lines = self.order_line.search([('product_id','=',dep_product),('order_id','=',sale.id)])
                for line in sale_dep_lines:
                    amt_inv = 0.00
                    amt_res = 0.00
                    #must find the invoice corresponding with the deposit and sum the amount - residual from the invoice.
                    for inv_line in line.invoice_lines:
                        invoice = inv_line.move_id
                        invoice_id = invoice.id
                        if invoice_id not in deposit_invs:
                            deposit_invs.append(invoice_id)
                            if invoice.state=='posted':
                                amt_res += invoice.amount_residual
                                amt_inv += invoice.amount_total
                                total_deps += (amt_inv - amt_res)                
                sale.deposit_total = total_deps
     
    @api.depends('order_line')     
    def _compute_bal_due(self):
        for sale in self:
            amt_res = 0.00
            amt_inv = 0.00
            for invoice in sale.invoice_ids:
                if invoice.state=='posted':
                    amt_res += invoice.amount_residual
                    amt_inv += invoice.amount_total
            amt_due = (sale.amount_total - amt_inv) + amt_res
            sale.inv_bal_due = amt_due
          
    @api.onchange('inv_bal_due')
    def _lock_sales_orders(self):
        done = True
        for sale in self:
            if sale.inv_bal_due <= 0.00:
                for line in sale.order_line:
                    if line.qty_delivered < line.product_uom_qty:
                        done = False
                        break
                if done:
                    sale.state = 'done'