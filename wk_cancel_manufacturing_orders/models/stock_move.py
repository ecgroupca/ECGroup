# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_is_zero


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _decrease_reserved_quanity(self, quantity):
        """ Decrease the reservation on move lines but keeps the
        all other data.
        """
        ctx = dict(self.env.context or {})
        if self.env.user.has_group('wk_cancel_manufacturing_orders.group_cancel_manufacturing_order') and ctx.get('force_cancel', False):
            move_line_to_unlink = self.env['stock.move.line']
            for move in self:
                move.state = 'cancel'
                reserved_quantity = quantity
                for move_line in move.move_line_ids:
                    if move_line.product_uom_qty > reserved_quantity:
                        move_line.product_uom_qty = reserved_quantity
                    else:
                        move_line.product_uom_qty = 0
                        reserved_quantity -= move_line.product_uom_qty
                    if not move_line.product_uom_qty and not move_line.qty_done:
                        move_line_to_unlink |= move_line
            move_line_to_unlink.unlink()
            return True
        else:
            return super(StockMove, self)._decrease_reserved_quanity(quantity)

    def _action_cancel(self):
        ctx = dict(self.env.context or {})
        if self.env.user.has_group('wk_cancel_manufacturing_orders.group_cancel_manufacturing_order') and ctx.get('force_cancel', False):
            # if any(move.state == 'done' and not move.scrapped for move in self):
            #     raise UserError(_('You cannot cancel a stock move that has been set to \'Done\'.'))
            moves_to_cancel = self.filtered(lambda m: m.state != 'cancel')
            # self cannot contain moves that are either cancelled or done, therefore we can safely
            # unlink all associated move_line_ids
            moves_to_cancel._do_unreserve()

            for move in moves_to_cancel:
                siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
                if move.propagate_cancel:
                    # only cancel the next move if all my siblings are also cancelled
                    if all(state == 'cancel' for state in siblings_states):
                        move.move_dest_ids.filtered(lambda m: m.state != 'done')._action_cancel()
                else:
                    if all(state in ('done', 'cancel') for state in siblings_states):
                        move.move_dest_ids.write({'procure_method': 'make_to_stock'})
                        move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})
            self.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})
            return True
        else:
            return super(StockMove, self)._action_cancel()
