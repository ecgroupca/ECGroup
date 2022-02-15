# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api
import datetime

         
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    trans_shipped_date = fields.Datetime(
        'Shipped Date',
        compute = '_get_shipped_date',
        )
        
    @api.depends('picking_ids')
    def _get_shipped_date(self):
        for sale in self:
            all_ship_dates = []
            for pick in sale.picking_ids:
                all_ship_dates.append(pick.x_bol_date or pick.date_done)    
            ship_dates = [d for d in all_ship_dates if isinstance(d, datetime.date)]  
            if ship_dates:            
                sale.trans_shipped_date = max(ship_dates)  
            else:
                sale.trans_shipped_date = False