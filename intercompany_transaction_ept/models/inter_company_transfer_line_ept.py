"""
For inter_company_transfer_ept module.
"""
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class InterCompanyTransferLine(models.Model):
    """
    Model for inter company transfer lines.
    @author: Maulik Barad on Date 24-Sep-2019.
    """
    _name = "inter.company.transfer.line.ept"
    _description = "Inter Company Transfer Line"

    inter_company_transfer_id = fields.Many2one('inter.company.transfer.ept')
    product_id = fields.Many2one('product.product')
    quantity = fields.Float(default=1.0)
    delivered_qty = fields.Float(compute='_get_delivered_qty', string='Delivered Quantity',
                                 store=True, readonly=True, digits="Product Unit of Measure")
    price = fields.Float(string='Price')

    @api.constrains('quantity')
    def _check_quantity(self):
        """
        Constraint for checking the quantity.
        @author: Maulik Barad on Date 27-Sep-2019.
        """
        for line in self:
            if not line.quantity > 0:
                raise ValidationError("Quantity can't be zero or negative.")

    @api.depends('inter_company_transfer_id.picking_ids.state')
    def _get_delivered_qty(self):
        """
        Method for counting the delivered quantity.
        @author: Maulik Barad on Date 24-Sep-2019.
        """
        for line in self:
            delivered_qty = 0.0
            if line.inter_company_transfer_id.state == 'processed':
                for picking_id in line.inter_company_transfer_id.picking_ids.filtered(
                        lambda x: x.state != 'cancel' and x.picking_type_id.code == 'incoming'):
                    for move in picking_id.move_ids_without_package:
                        if line.product_id == move.product_id:
                            delivered_qty += move.product_id.uom_id._compute_quantity(
                                move.quantity_done, move.product_id.uom_id)
            line.delivered_qty = delivered_qty

    @api.onchange('product_id', 'inter_company_transfer_id')
    def default_price_get(self):
        """
        Sets price of product in ICT line.
        @author: Maulik Barad on Date 24-Sep-2019.
        """
        for line in self:
            if line.product_id:
                pricelist_id = line.inter_company_transfer_id.pricelist_id
                if pricelist_id:
                    line.price = pricelist_id.price_get(
                        line.product_id.id, line.quantity)[pricelist_id.id]
                else:
                    line.price = line.product_id.lst_price
            else:
                line.price = 0.0
