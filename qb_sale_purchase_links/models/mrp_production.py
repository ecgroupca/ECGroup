# Copyright 2018 Alex Comba - Agile Business Group
# Copyright 2016-2018 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    
    purchase_order_count = fields.Integer(
        "Count of generated PO",
        compute='_compute_purchase_order_count',
        groups='purchase.group_purchase_user')

    @api.depends('procurement_group_id.stock_move_ids.created_purchase_line_id.order_id', 'procurement_group_id.stock_move_ids.move_orig_ids.purchase_line_id.order_id')
    def _compute_purchase_order_count(self):
        for production in self:
            production.purchase_order_count = len(production.procurement_group_id.stock_move_ids.created_purchase_line_id.order_id |
                                                  production.procurement_group_id.stock_move_ids.move_orig_ids.purchase_line_id.order_id)