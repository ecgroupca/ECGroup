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
        res = super().button_mark_done()
        if res:
            self.rma_id.state = 'repaired'
        return res

