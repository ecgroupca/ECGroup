# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    deposit_total = fields.Float(
        'Total Deposits', 
        compute="_compute_deps_total",
        )
    
    def _compute_deps_total(self):
        for sale in self:
            total_deps = 0
            company_id = sale.company_id
            config = self.env['res.config.settings']
            setting = config.search(company_id=company_id)
            setting = setting and setting[0] or None
            dep_product = setting and setting.deposit_default_product_id or None
            if dep_product:
                for line in sale.order_line:
                    if line.product_id == dep_product:
                        total_deps += line.price_total
                deposit_total = total_deps
                
