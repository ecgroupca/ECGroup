# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools


class StockPicking(models.Model):
    """Stock Picking"""

    _inherit = 'stock.picking'
    
    location_id = fields.Many2one(readonly=False)
    location_dest_id = fields.Many2one(readonly=False)
    
    
    @api.onchange('location_id')
    def _onchange_sales_team(self):
        for picking in self:
            for move in picking.move_lines:
                move.location_id = picking.location_id
                move.location_dest_id = picking.location_dest_id
            