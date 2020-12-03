# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    deposit_total = fields.Float(
        'Total Deposits', 
        compute="_compute_deps_total",
        )
    
    @api.depends('order_line')
    def _compute_deps_total(self):
        for sale in self:
            total_deps = 0
            company_id = sale.company_id and sale.company_id.id or 1
            config = self.env['ir.config_parameter']
            setting = config.search([('key','=','sale.default_deposit_product_id')])
            setting = setting and setting[0] or None
            dep_product = setting and setting.value or None
            if dep_product:
                for line in sale.order_line:
                    if str(line.product_id.id) == dep_product:
                        total_deps += abs(line.price_unit)
            sale.deposit_total = total_deps
                
