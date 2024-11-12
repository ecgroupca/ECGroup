# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict
from datetime import datetime
from dateutil import relativedelta
from itertools import groupby
from operator import itemgetter
from re import findall as regex_findall, split as regex_split

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
import logging
from odoo import models, fields, api
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    """Stock Picking"""

    _inherit = 'stock.picking'
    
    location_id = fields.Many2one(readonly=False)
    location_dest_id = fields.Many2one(readonly=False)
    bypass_reservation = fields.Boolean(
        'Bypass Reservations',
        )
    
    @api.onchange('location_id','location_dest_id')
    def _onchange_locations(self):
        for picking in self:
            for move in picking.move_ids:
                move.location_id = picking.location_id
                move.location_dest_id = picking.location_dest_id
            for move_l in picking.move_line_ids:
                move_l.location_id = picking.location_id
                move_l.location_dest_id = picking.location_dest_id   
      
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    bypass_reservation = fields.Boolean('Bypass Reservation')     

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    bypass_reservation = fields.Boolean(
        'Bypass Reservation',
        compute = '_compute_bypass',
        readonly = False,
        store=True,
        )
        
    @api.depends('move_id')
    def _compute_bypass(self):
        for move_line in self:
            move = move_line.move_id          
            move_line.bypass_reservation = move and move.bypass_reservation or False

class StockMove(models.Model):
    _inherit = 'stock.move'

    bypass_reservation = fields.Boolean(
        'Bypass Reservation',
        compute = '_compute_bypass',
        readonly = False,
        store=True,
        )
        
    @api.depends('product_id')
    def _compute_bypass(self):
        for move in self:
            move.bypass_reservation = move.product_id and move.product_id.bypass_reservation or False