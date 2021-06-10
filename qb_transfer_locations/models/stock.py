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
    picking_type_id = fields.Many2one(readonly=False)
    
    @api.onchange('location_id','location_dest_id')
    def _onchange_sales_team(self):
        for picking in self:
            for move in picking.move_lines:
                move.location_id = picking.location_id
                move.location_dest_id = picking.location_dest_id
            for move_l in picking.move_line_ids:
                move_l.location_id = picking.location_id
                move_l.location_dest_id = picking.location_dest_id                    