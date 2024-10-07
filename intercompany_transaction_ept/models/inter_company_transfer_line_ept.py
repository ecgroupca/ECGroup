# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
   
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InterCompanyTransferLine(models.Model):
    """
    Model for inter company transfer lines.
    @author: Maulik Barad.
    """
    _name = "inter.company.transfer.line.ept"
    _description = "Inter Company Transfer Line"

    inter_company_transfer_id = fields.Many2one("inter.company.transfer.ept")
    product_id = fields.Many2one("product.product")
    quantity = fields.Float(default=1.0)
    delivered_qty = fields.Float(compute="_compute_delivered_qty", string="Delivered Quantity", store=True,
                                 readonly=True, digits="Product Unit of Measure")
    price = fields.Float("Unit Price")
    lot_serial_ids = fields.Many2many("stock.lot", string="Lot/Serial", copy=False)
    purchase_line_ids = fields.One2many("purchase.order.line", "ict_line_id", copy=False)

    @api.constrains("quantity", "lot_serial_ids")
    def _check_quantity(self):
        """
        Constraint for checking the quantity.
        @author: Maulik Barad on Date 22-Jan-21.
        """
        for line in self:
            if not line.quantity > 0:
                raise ValidationError(_("Quantity can't be zero or negative."))
            if line.lot_serial_ids and line.product_id.tracking == "serial":
                if line.quantity > len(line.lot_serial_ids):
                    raise ValidationError(_("Provided Serial numbers can't fulfill the given Quantity for Product - "
                                            "%s.\nAdd more Serial numbers to fulfill the quantity.") %
                                          line.product_id.name)

    @api.depends("inter_company_transfer_id.picking_ids.state", "purchase_line_ids.qty_received")
    def _compute_delivered_qty(self):
        """
        Method for counting the delivered quantity.
        @author: Maulik Barad.
        """
        for line in self:
                               
            ict = line.inter_company_transfer_id
            if ict.type == "ict":
                delivered_qty = 0.0
                for po_line in line.purchase_line_ids:
                    delivered_qty += po_line.qty_received
                line.delivered_qty = delivered_qty
            else:
                delivered_qty = 0.0
                for picking in ict.picking_ids.filtered(
                                   
                                                      
                                                         
                                                  
                 
                                   
                                                        
                        lambda x: x.state == "done" and x.picking_type_id.code == "incoming"):
                    for move_line in picking.move_line_ids.filtered(lambda x: x.product_id == line.product_id):
                        if not line.lot_serial_ids or (line.lot_serial_ids and move_line.lot_id.name in
                                                       line.lot_serial_ids.mapped("name")):
                            delivered_qty += move_line.qty_done
                line.delivered_qty = delivered_qty

    @api.onchange("product_id", "inter_company_transfer_id")
    def default_price_get(self):
        """
        Sets price of product in ICT line.
        @author: Maulik Barad.
        """
        for line in self:
            if line.product_id:
                pricelist_id = line.inter_company_transfer_id.pricelist_id
                if pricelist_id:
                    line.price = pricelist_id._get_product_price(line.product_id, line.quantity)
                                                                           
                else:
                    line.price = line.product_id.lst_price
            else:
                line.price = 0.0
