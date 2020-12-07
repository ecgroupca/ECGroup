# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    reseller_id = fields.Char(
        'Reseller ID'
        )
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    comm_rate = fields.Float(
        'Commissin Rate (%)', 
        )

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    deposit_total = fields.Float(
        'Total Deposits', 
        compute="_compute_deps_total",
        )
    customer_code = fields.Char(
        'Customer Code'
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
            
            
            