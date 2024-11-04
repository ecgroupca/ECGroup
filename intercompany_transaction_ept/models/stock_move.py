# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields
from odoo.tools.float_utils import float_is_zero


class StockMove(models.Model):
    """
    Inherited for passing values to picking.
    @author: Maulik Barad.
    """
    _inherit = "stock.move"

    auto_ict_id = fields.Many2one('inter.company.transfer.ept', string="Resupply ICT", copy=False,
                                  help="Reference of Resupply ICT.")

    def _get_new_picking_values(self):
        """
        Inherited for adding relation with ICT if created by it.
        @author: Maulik Barad.
        @return: Dictionary for creating picking.
        """
        vals = super(StockMove, self)._get_new_picking_values()
        if self.sale_line_id.order_id.inter_company_transfer_id:
            vals.update({"inter_company_transfer_id": self.sale_line_id.order_id.inter_company_transfer_id.id})
        return vals

    def _action_assign(self, force_qty=False):
        """
        This method is inherited for assigning the same lot/serial to SO's moves as same as ICT lines.
        @author: Maulik Barad on Date 25-Dec-2020.
        """
        if self.picking_id and self.picking_id.inter_company_transfer_id and \
                "incoming" in self.picking_id.picking_type_id.mapped("code") and self.move_orig_ids and \
                all(all(origin_move.state != "done" for origin_move in move.move_orig_ids) for move in self):
            return False

        res = super(StockMove, self)._action_assign(force_qty=force_qty)

        self.unreserve_manual_moves()

        move_line_vals_list = []
        assigned_moves = self.env["stock.move"]
        for move in self.filtered(lambda m: m.state not in ["draft", "done", "cancel"]):
            customer_move = move.get_ict_customer_move()
            ict = move.picking_id.inter_company_transfer_id

            ict_sale_lot_assign, ict_purchase_lot_assign, ict_internal_lot_assign, reverse_sale_ict_lot_assign, \
                reverse_po_ict_lot_assign = move.check_ict_move(customer_move, ict)

            if ict_sale_lot_assign or ict_internal_lot_assign or reverse_po_ict_lot_assign:
                if ict_sale_lot_assign:
                    ict_lines = customer_move.sale_line_id.ict_line_id
                else:
                    if ict_internal_lot_assign:
                        ict = customer_move.picking_id.inter_company_transfer_id
                    ict_lines = ict.inter_company_transfer_line_ids.filtered(lambda x: x.product_id == move.product_id)
                need = move.create_ict_sale_lot_move_lines(ict_lines)
                if need < move.product_uom_qty:
                    assigned_moves |= move

            if ict_purchase_lot_assign or reverse_sale_ict_lot_assign:
                move_line_vals = move.prepare_ict_lot_move_lines(reverse_sale_ict_lot_assign)

                if move_line_vals:
                    move_line_vals_list += move_line_vals
                    assigned_moves |= move

        self.env["stock.move.line"].create(move_line_vals_list)
        assigned_moves.write({"state": "assigned"})
        return res

    def unreserve_manual_moves(self):
        """
        This method is used to unreserve the moves at once, which speeds up the process.
        @author: Maulik Barad on Date 30-Mar-2021.
        """
        need_to_unreserve = []
        for move in self.filtered(lambda m: m.state not in ["draft", "done", "cancel"]):
            unreserve = False
            customer_move = move.get_ict_customer_move()
            ict = move.picking_id.inter_company_transfer_id

            ict_sale_lot_assign, ict_purchase_lot_assign, ict_internal_lot_assign, reverse_sale_ict_lot_assign, \
                reverse_po_ict_lot_assign = move.check_ict_move(customer_move, ict)

            if ict_sale_lot_assign or ict_internal_lot_assign or reverse_po_ict_lot_assign:
                if ict_sale_lot_assign:
                    ict_lines = customer_move.sale_line_id.ict_line_id
                else:
                    if ict_internal_lot_assign:
                        ict = customer_move.picking_id.inter_company_transfer_id
                    ict_lines = ict.inter_company_transfer_line_ids.filtered(lambda x: x.product_id == move.product_id)
                if ict_lines.lot_serial_ids:
                    unreserve = True

            elif reverse_sale_ict_lot_assign and move.product_id.tracking != "none":
                unreserve = True
            elif ict_purchase_lot_assign and move.move_orig_ids.filtered(lambda x: x.state == "done").lot_ids:
                unreserve = True

            if unreserve:
                need_to_unreserve.append(move.id)
        # Unreserve all moves, which needed to assign Manually.
        self.env["stock.move"].browse(need_to_unreserve)._do_unreserve()
        return True

    def get_ict_customer_move(self):
        """
        This method is used to get the move, which is connected to the sale order line.
        This method is useful, when there will be multi step picking.
        @author: Maulik Barad on Date 26-Dec-2020.
        """
        customer_move = self
        if not customer_move.sale_line_id:
            if customer_move.move_dest_ids and customer_move.move_dest_ids.sale_line_id:
                customer_move = customer_move.move_dest_ids
            elif customer_move.move_dest_ids.move_dest_ids and \
                    customer_move.move_dest_ids.move_dest_ids.sale_line_id:
                customer_move = customer_move.move_dest_ids.move_dest_ids
        return customer_move

    def check_ict_move(self, customer_move, ict):
        """
        This method is used to check the move and get the type of it for manually assigning.
        @author: Maulik Barad on Date 30-Mar-2021.
        """
        ict_sale_lot_assign = bool(customer_move.sale_line_id.ict_line_id and not self.move_orig_ids)
        ict_purchase_lot_assign = bool(
            ict and ict.type == "ict" and not ict.reverse_inter_company_transfer_ids and self.purchase_line_id)
        ict_internal_lot_assign = bool(ict and not self.move_orig_ids and ict.type in ["internal", "int_reverse"])
        reverse_sale_ict_lot_assign = bool(ict and ict.type == "ict_reverse" and self.sale_line_id)
        reverse_po_ict_lot_assign = bool(ict and ict.type == "ict_reverse" and
                                         self.location_id == self.picking_type_id.warehouse_id.lot_stock_id)
        return ict_sale_lot_assign, ict_purchase_lot_assign, ict_internal_lot_assign, reverse_sale_ict_lot_assign, \
            reverse_po_ict_lot_assign

    def create_ict_sale_lot_move_lines(self, ict_lines):
        """
        This method will create move line for particular lot/serials from ICT line.
        @param ict_lines: ICT lines related to Move.
        @author: Maulik Barad on Date 29-Dec-2020.
        """
        self.ensure_one()
        need = self.product_uom_qty

        if not ict_lines.lot_serial_ids:
            return need
        # self._do_unreserve()
        for ict_line in ict_lines:
            qty = ict_line.quantity
            for lot_serial_id in ict_line.lot_serial_ids:
                available_quantity = self._get_available_quantity(self.location_id, lot_serial_id)
                if available_quantity <= 0:
                    continue
                taken_quantity = self._update_reserved_quantity(qty, available_quantity, self.location_id,
                                                                lot_serial_id, strict=False)
                need -= taken_quantity
                qty -= taken_quantity
                if float_is_zero(need, precision_rounding=self.product_id.uom_id.rounding):
                    return need
        return need

    def prepare_ict_lot_move_lines(self, reverse=False):
        """
        This method is used to prepare the move line data with specific lot/serial from the origin move of the sale.
        @author: Maulik Barad on Date 29-Dec-2020.
        """
        self.ensure_one()

        move_line_vals = []
        need = self.product_uom_qty

        # if reverse and self.product_id.tracking != "none":
        #     self._do_unreserve()
        origin_moves = self.move_orig_ids.filtered(lambda x: x.state == "done").sorted(lambda x: x.id)
        dest_moves = []
        for origin_move in origin_moves:
            other_moves = (origin_move.move_dest_ids.sorted(lambda x: x.id) - self).filtered(
                lambda x: x not in dest_moves)
            available_qty = origin_move.quantity_done

            for dest_move in other_moves:
                for move_line in dest_move.move_line_ids:
                    if (move_line.lot_id.name in origin_move.lot_ids.mapped(
                            "name") or not move_line.lot_id) and move_line.qty_done <= available_qty:
                        dest_moves.append(dest_move)
                        available_qty -= move_line.qty_done

            if available_qty <= 0:
                continue

            move_lines = origin_move.move_line_ids.filtered(lambda x: x.lot_id)
            if move_lines:
                self._do_unreserve()
            else:
                self.quantity_done = origin_move.quantity_done

            for move_line in move_lines:
                quantity = min(move_line.qty_done, need)
                vals = self._prepare_move_line_vals(quantity=quantity)
                vals.update({'qty_done':quantity})
                lot_name = move_line.lot_id.name
                if move_line.product_id.tracking in ["lot", "serial"]:
                    lot_serial = self.env["stock.lot"].search([("company_id", "=", vals.get("company_id")),
                                                               ("product_id", "=", vals.get("product_id")),
                                                               ("name", "=", lot_name)], limit=1)
                    if lot_serial and (move_line.product_id.tracking == "lot" or lot_serial.product_qty == 0.0):
                        vals.update({"lot_id": lot_serial.id})
                if not vals.get("lot_id"):
                    vals.update({"lot_name": lot_name})
                move_line_vals.append(vals)
                need -= quantity
                if float_is_zero(need, precision_rounding=self.product_id.uom_id.rounding):
                    break

        return move_line_vals

    def _prepare_phantom_move_values(self, bom_line, product_qty, quantity_done):
        """
        Inherited for setting the origin moves with PO's moves, when product is of BoM type.
        @author: Maulik Barad on Date 23-Feb-2021.
        """
        vals = super(StockMove, self)._prepare_phantom_move_values(bom_line, product_qty, quantity_done)

        if self.picking_id.inter_company_transfer_id:
            origin_picking = self.picking_id.inter_company_transfer_id.picking_ids.filtered(
                lambda x: x.location_dest_id.usage == "customer" and x.state != "cancel")
            origin_move = origin_picking.move_ids.filtered(lambda x:
                                                           x.product_id.id == vals.get("product_id") and
                                                           x.product_uom_qty == vals.get("product_uom_qty"))
            if len(origin_move) > 1:
                origin_move = origin_move.filtered(lambda x: x.sale_line_id.ict_line_id == self.ict_line_id)
            if origin_move:
                vals["move_orig_ids"] = [(6, 0, origin_move.ids)]

        return vals
