# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import models, fields, api
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
    approx_lead_time = fields.Float(
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
            total_deps = 0
            total_comm = 0
            company_id = sale.company_id and sale.company_id.id or 1
            config = self.env['ir.config_parameter']
            setting = config.search([('key','=','sale.default_deposit_product_id')])
            setting = setting and setting[0] or None
            dep_product = setting and setting.value or None
            for line in sale.order_line:
                if dep_product and str(line.product_id.id) == dep_product:
                    total_deps += abs(line.price_unit)
                if line.comm_rate:
                    total_comm += line.comm_rate*line.price_unit*line.product_uom_qty/100
            sale.comm_total = total_comm        
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