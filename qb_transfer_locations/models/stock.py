# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import models, fields, api
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    """Stock Picking"""

    _inherit = 'stock.picking'
    
    location_id = fields.Many2one(readonly=False)
    location_dest_id = fields.Many2one(readonly=False)
    
    @api.onchange('location_id','location_dest_id')
    def _onchange_locations(self):
        for picking in self:
            for move in picking.move_lines:
                move.location_id = picking.location_id
                move.location_dest_id = picking.location_dest_id
            for move_l in picking.move_line_ids:
                move_l.location_id = picking.location_id
                move_l.location_dest_id = picking.location_dest_id   
      
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    bypass_reservation = fields.Boolean('Bypass Reservation')                

class StockMove(models.Model):
    _inherit = 'stock.move'

    bypass_reservation = fields.Boolean('Bypass Reservation')

    def _should_bypass_reservation(self):
        self.ensure_one()
        bypass = self.location_id.should_bypass_reservation() 
        bypass |= self.product_id.type != 'product'
        bypass |= self.product_id.bypass_reservation
        bypass |= self.bypass_reservation
        return bypass