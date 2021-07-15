# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api

         
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    trans_shipped_date = fields.Datetime(
        'Shipped Date',
        compute = '_get_shipped_date',
        )
        