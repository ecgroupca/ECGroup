# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    ict_line_id = fields.Many2one("inter.company.transfer.line.ept")

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        """
        This method inherited to set the origin moves of SO picking in PO picking.
        @author: Maulik Barad on Date 24-Dec-2020.
        """
        vals = super(PurchaseOrderLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty,
                                                                       product_uom)
        if picking.inter_company_transfer_id:
            origin_picking = picking.inter_company_transfer_id.picking_ids.filtered(
                lambda x: x.location_dest_id.usage == "customer" and x.state != "cancel")
            origin_move = origin_picking.move_ids.filtered(lambda x:
                                                             x.product_id.id == vals.get("product_id") and
                                                             x.product_uom_qty == vals.get("product_uom_qty"))
            if len(origin_move) > 1:
                origin_move = origin_move.filtered(lambda x: x.sale_line_id.ict_line_id == self.ict_line_id)
            if origin_move:
                vals["move_orig_ids"] = [(6, 0, origin_move.ids)]
        return vals
