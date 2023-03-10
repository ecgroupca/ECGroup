# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MRPProduction(models.Model):
    _inherit = "mrp.production"

    # RMA that created the repair (Manufacturing Order)
    rma_id = fields.Many2one(comodel_name="rma", string="RMA Repair", copy=False,)


    def _action_cancel(self):
        res = super()._action_cancel()
        # A stock user could have no RMA permissions, so the ids wouldn't
        # be accessible due to record rules.
        cancelled_moves = self.filtered(lambda r: r.state == "cancel").sudo()
        cancelled_moves.mapped("rma_id").update_repaired_state()
        self.rma_id.state = 'received'
        return res

    def button_mark_done(self):
        self.ensure_one()
        self._check_company()
        for wo in self.workorder_ids:
            if wo.time_ids.filtered(lambda x: (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
                raise UserError(_('Work order %s is still running') % wo.name)
        self._check_lots()

        self.post_inventory()
        # Moves without quantity done are not posted => set them as done instead of canceling. In
        # case the user edits the MO later on and sets some consumed quantity on those, we do not
        # want the move lines to be canceled.
        (self.move_raw_ids | self.move_finished_ids).filtered(lambda x: x.state not in ('done', 'cancel')).write({
            'state': 'done',
            'product_uom_qty': 0.0,
        })
        self.rma_id.state = 'repaired'
        return self.write({'date_finished': fields.Datetime.now()})
        
    def post_inventory(self):
        for order in self:
            # In case the routing allows multiple WO running at the same time, it is possible that
            # the quantity produced in one of the workorders is lower than the quantity produced in
            # the MO.
            if order.product_id.tracking != "none" and any(
                wo.state not in ["done", "cancel"]
                and float_compare(wo.qty_produced, order.qty_produced, precision_rounding=order.product_uom_id.rounding) == -1
                for wo in order.workorder_ids
            ):
                raise UserError(
                    _(
                        "At least one work order has a quantity produced lower than the quantity produced in the manufacturing order. "
                        + "You must complete the work orders before posting the inventory."
                    )
                )

            if not any(order.move_raw_ids.mapped('quantity_done')):
                raise UserError(_("You must indicate a non-zero amount consumed for at least one of your components"))

            moves_not_to_do = order.move_raw_ids.filtered(lambda x: x.state == 'done')
            moves_to_do = order.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            for move in moves_to_do.filtered(lambda m: m.product_qty == 0.0 and m.quantity_done > 0):
                move.product_uom_qty = move.quantity_done
            # MRP do not merge move, catch the result of _action_done in order
            # to get extra moves.
            moves_to_do = moves_to_do._action_done()
            moves_to_do = order.move_raw_ids.filtered(lambda x: x.state == 'done') - moves_not_to_do
            order._cal_price(moves_to_do)
            moves_to_finish = order.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            moves_to_finish = moves_to_finish._action_done()
            order.workorder_ids.mapped('raw_workorder_line_ids').unlink()
            order.workorder_ids.mapped('finished_workorder_line_ids').unlink()
            order.action_assign()
            consume_move_lines = moves_to_do.mapped('move_line_ids')
            for moveline in moves_to_finish.mapped('move_line_ids'):
                if moveline.move_id.has_tracking != 'none' and moveline.product_id == order.product_id or moveline.lot_id in consume_move_lines.mapped('lot_produced_ids'):
                    if any([not ml.lot_produced_ids for ml in consume_move_lines]):
                        raise UserError(_('You can not consume without telling for which lot you consumed it'))
                    # Link all movelines in the consumed with same lot_produced_ids false or the correct lot_produced_ids
                    filtered_lines = consume_move_lines.filtered(lambda ml: moveline.lot_id in ml.lot_produced_ids)
                    moveline.write({'consume_line_ids': [(6, 0, [x for x in filtered_lines.ids])]})
                else:
                    # Link with everything
                    moveline.write({'consume_line_ids': [(6, 0, [x for x in consume_move_lines.ids])]})
        return True

