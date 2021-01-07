# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import models, fields, api
_logger = logging.getLogger(__name__)

class CRMTeam(models.Model):
    _inherit = 'crm.team'
    
    default_comm_rate = fields.Float(
        'Default Commissin Rate (%)', 
        readonly = False,
        )

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    reseller_id = fields.Char(
        'Reseller ID'
        )
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    comm_rate = fields.Float(
        'Commissin Rate (%)', 
        #compute="_compute_comm_rate",        
        )
        
    """@api.depends('order_id')
    def _compute_comm_rate(self):
        for line in self:
            if line.order_id.team_id and line.order_id.team_id.default_comm_rate:
                line.comm_rate = line.order_id.team_id.default_comm_rate"""
                
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    deposit_total = fields.Float(
        'Total Deposits', 
        compute="_compute_deps_total",
        )
    approx_lead_time = fields.Float(
        'Approximate Lead Time'
        )
    sidemark = fields.Char(
        'Sidemark'
        )       
    comm_total = fields.Float(
        'Total Commisions', 
        compute="_compute_deps_total",
        )
    inv_bal_due = fields.Float(
        'Balance Due',
        compute="_compute_bal_due",
        )
        

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