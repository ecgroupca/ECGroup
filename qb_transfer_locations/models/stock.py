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
        
    def _action_assign(self):
        """ Reserve stock moves by creating their stock move lines. A stock move is
        considered reserved once the sum of `product_qty` for all its move lines is
        equal to its `product_qty`. If it is less, the stock move is considered
        partially available.
        """
        assigned_moves = self.env['stock.move']
        partially_available_moves = self.env['stock.move']
        # Read the `reserved_availability` field of the moves out of the loop to prevent unwanted
        # cache invalidation when actually reserving the move.
        reserved_availability = {move: move.reserved_availability for move in self}
        roundings = {move: move.product_id.uom_id.rounding for move in self}
        move_line_vals_list = []
        for move in self.filtered(lambda m: m.state in ['confirmed', 'waiting', 'partially_available']):
            if not move.bypass_reservation or (move.bypass_reservation and move._should_bypass_reservation()):               
                rounding = roundings[move]
                missing_reserved_uom_quantity = move.product_uom_qty - reserved_availability[move]
                missing_reserved_quantity = move.product_uom._compute_quantity(missing_reserved_uom_quantity, move.product_id.uom_id, rounding_method='HALF-UP')
                if move._should_bypass_reservation():
                    # create the move line(s) but do not impact quants
                    if move.product_id.tracking == 'serial' and (move.picking_type_id.use_create_lots or move.picking_type_id.use_existing_lots):
                        for i in range(0, int(missing_reserved_quantity)):
                            move_line_vals_list.append(move._prepare_move_line_vals(quantity=1))
                    else:
                        to_update = move.move_line_ids.filtered(lambda ml: ml.product_uom_id == move.product_uom and
                                                                ml.location_id == move.location_id and
                                                                ml.location_dest_id == move.location_dest_id and
                                                                ml.picking_id == move.picking_id and
                                                                not ml.lot_id and
                                                                not ml.package_id and
                                                                not ml.owner_id)
                        if to_update:
                            to_update[0].product_uom_qty += missing_reserved_uom_quantity
                        else:
                            move_line_vals_list.append(move._prepare_move_line_vals(quantity=missing_reserved_quantity))
                    assigned_moves |= move
                else:
                    if float_is_zero(move.product_uom_qty, precision_rounding=move.product_uom.rounding):
                        assigned_moves |= move
                    elif not move.move_orig_ids:
                        if move.procure_method == 'make_to_order':
                            continue
                        # If we don't need any quantity, consider the move assigned.
                        need = missing_reserved_quantity
                        if float_is_zero(need, precision_rounding=rounding):
                            assigned_moves |= move
                            continue
                        # Reserve new quants and create move lines accordingly.
                        forced_package_id = move.package_level_id.package_id or None
                        available_quantity = self.env['stock.quant']._get_available_quantity(move.product_id, move.location_id, package_id=forced_package_id)
                        if available_quantity <= 0:
                            continue
                        taken_quantity = move._update_reserved_quantity(need, available_quantity, move.location_id, package_id=forced_package_id, strict=False)
                        if float_is_zero(taken_quantity, precision_rounding=rounding):
                            continue
                        if float_compare(need, taken_quantity, precision_rounding=rounding) == 0:
                            assigned_moves |= move
                        else:
                            partially_available_moves |= move
                    else:
                        # Check what our parents brought and what our siblings took in order to
                        # determine what we can distribute.
                        # `qty_done` is in `ml.product_uom_id` and, as we will later increase
                        # the reserved quantity on the quants, convert it here in
                        # `product_id.uom_id` (the UOM of the quants is the UOM of the product).
                        move_lines_in = move.move_orig_ids.filtered(lambda m: m.state == 'done').mapped('move_line_ids')
                        keys_in_groupby = ['location_dest_id', 'lot_id', 'result_package_id', 'owner_id']

                        def _keys_in_sorted(ml):
                            return (ml.location_dest_id.id, ml.lot_id.id, ml.result_package_id.id, ml.owner_id.id)

                        grouped_move_lines_in = {}
                        for k, g in groupby(sorted(move_lines_in, key=_keys_in_sorted), key=itemgetter(*keys_in_groupby)):
                            qty_done = 0
                            for ml in g:
                                qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                            grouped_move_lines_in[k] = qty_done
                        move_lines_out_done = (move.move_orig_ids.mapped('move_dest_ids') - move)\
                            .filtered(lambda m: m.state in ['done'])\
                            .mapped('move_line_ids')
                        # As we defer the write on the stock.move's state at the end of the loop, there
                        # could be moves to consider in what our siblings already took.
                        moves_out_siblings = move.move_orig_ids.mapped('move_dest_ids') - move
                        moves_out_siblings_to_consider = moves_out_siblings & (assigned_moves + partially_available_moves)
                        reserved_moves_out_siblings = moves_out_siblings.filtered(lambda m: m.state in ['partially_available', 'assigned'])
                        move_lines_out_reserved = (reserved_moves_out_siblings | moves_out_siblings_to_consider).mapped('move_line_ids')
                        keys_out_groupby = ['location_id', 'lot_id', 'package_id', 'owner_id']

                        def _keys_out_sorted(ml):
                            return (ml.location_id.id, ml.lot_id.id, ml.package_id.id, ml.owner_id.id)

                        grouped_move_lines_out = {}
                        for k, g in groupby(sorted(move_lines_out_done, key=_keys_out_sorted), key=itemgetter(*keys_out_groupby)):
                            qty_done = 0
                            for ml in g:
                                qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                            grouped_move_lines_out[k] = qty_done
                        for k, g in groupby(sorted(move_lines_out_reserved, key=_keys_out_sorted), key=itemgetter(*keys_out_groupby)):
                            grouped_move_lines_out[k] = sum(self.env['stock.move.line'].concat(*list(g)).mapped('product_qty'))
                        available_move_lines = {key: grouped_move_lines_in[key] - grouped_move_lines_out.get(key, 0) for key in grouped_move_lines_in.keys()}
                        # pop key if the quantity available amount to 0
                        available_move_lines = dict((k, v) for k, v in available_move_lines.items() if v)

                        if not available_move_lines:
                            continue
                        for move_line in move.move_line_ids.filtered(lambda m: m.product_qty):
                            if available_move_lines.get((move_line.location_id, move_line.lot_id, move_line.result_package_id, move_line.owner_id)):
                                available_move_lines[(move_line.location_id, move_line.lot_id, move_line.result_package_id, move_line.owner_id)] -= move_line.product_qty
                        for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
                            need = move.product_qty - sum(move.move_line_ids.mapped('product_qty'))
                            # `quantity` is what is brought by chained done move lines. We double check
                            # here this quantity is available on the quants themselves. If not, this
                            # could be the result of an inventory adjustment that removed totally of
                            # partially `quantity`. When this happens, we chose to reserve the maximum
                            # still available. This situation could not happen on MTS move, because in
                            # this case `quantity` is directly the quantity on the quants themselves.
                            available_quantity = self.env['stock.quant']._get_available_quantity(
                                move.product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
                            if float_is_zero(available_quantity, precision_rounding=rounding):
                                continue
                            taken_quantity = move._update_reserved_quantity(need, min(quantity, available_quantity), location_id, lot_id, package_id, owner_id)
                            if float_is_zero(taken_quantity, precision_rounding=rounding):
                                continue
                            if float_is_zero(need - taken_quantity, precision_rounding=rounding):
                                assigned_moves |= move
                                break
                            partially_available_moves |= move
                if move.product_id.tracking == 'serial':
                    move.next_serial_count = move.product_uom_qty

            self.env['stock.move.line'].create(move_line_vals_list)
            partially_available_moves.write({'state': 'partially_available'})
            assigned_moves.write({'state': 'assigned'})
            self.mapped('picking_id')._check_entire_pack()