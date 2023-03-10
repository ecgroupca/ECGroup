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

