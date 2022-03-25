# Copyright 2022 Quickbeam ERP, Adam O'Connor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    #RMA linked to this sale
    rma_id = fields.Many2one(
        'rma', 
        string="RMA", 
        copy=False,
    )

    def action_view_rma(self):
        self.ensure_one()
        action = self.env.ref("rma.rma_action").read()[0]
        rma = self.rma_id
        action.update(
            res_id=rma.id, 
            view_mode="form",
            view_id=False, 
            views=False,)
        return action