# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api
import datetime

         
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    trans_shipped_date = fields.Datetime(
        'Shipped Date',
        compute = '_get_shipped_date',
        store = True,
        )
        
    @api.depends('picking_ids')
    def _get_shipped_date(self):
        for purchase in self:
            all_ship_dates = []
            for pick in purchase.picking_ids:
                all_ship_dates.append(pick.date_done)    
            ship_dates = [d for d in all_ship_dates if isinstance(d, datetime.date)]  
            if ship_dates:            
                purchase.trans_shipped_date = max(ship_dates)  
            else:
                purchase.trans_shipped_date = False 