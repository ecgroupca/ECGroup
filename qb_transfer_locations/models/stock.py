# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools


class StockPicking(models.Model):
    """Stock Picking"""

    _inherit = 'stock.picking'
    
    location_id = fields.Many2one('stock.picking', readonly=False)
    location_dest_id = fields.Many2one('stock.picking', readonly=False)