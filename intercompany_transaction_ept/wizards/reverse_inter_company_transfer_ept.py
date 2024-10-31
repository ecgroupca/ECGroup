# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ReverseInterCompanyTransfer(models.TransientModel):
    """
    For creating reverse inter company transfer.
    @author: Maulik Barad.
    """
    _name = 'reverse.inter.company.transfer.ept'
    _description = 'Reverse Inter Company Transfer'

    inter_company_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT")
    company_id = fields.Many2one(related="inter_company_transfer_id.destination_company_id")
    reverse_ict_line_ids = fields.One2many('reverse.inter.company.transfer.line.ept',
                                           'reverse_ict_id')

    def action_create_reverse_process(self):
        """
        It creates Reverse Transfer for ICT and IWT.
        @author: Maulik Barad.
        """
        ict_line_vals = []

        reverse_vals = self.get_default_vals()
        reverse_ict = self.inter_company_transfer_id.copy(default=reverse_vals)

        for line in self.reverse_ict_line_ids:
            ict_line_vals.append({
                'inter_company_transfer_id': reverse_ict.id,
                'product_id': line.product_id.id,
                'quantity': line.quantity or 1,
                'price': line.price,
                "lot_serial_ids": line.lot_serial_ids
            })

        self.env['inter.company.transfer.line.ept'].create(ict_line_vals)

        if reverse_ict.auto_workflow_id.validate_pickings_reverse:
            reverse_ict.with_context(auto_process=True).process_ict()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'inter.company.transfer.ept',
            "res_id": reverse_ict.id,
            'views': [(False, 'form')],
            'name': 'Reverse ICTs',
            'target': 'current',
        }

    def get_reverse_type(self):
        """
        This method gives type to create the reverse ict record.
        @author: Maulik Barad on Date 29-Dec-2020.
        """
        reverse_type = "ict_reverse"
        if self.inter_company_transfer_id.type == "internal":
            reverse_type = "int_reverse"
        return reverse_type

    def get_default_vals(self):
        """
        This method prepares dict of values for creating the reverse ict.
        @author: Maulik Barad on Date 30-Dec-2020.
        """
        reverse_type = self.get_reverse_type()
        source_warehouse_id = self.inter_company_transfer_id.destination_warehouse_id.id
        destination_warehouse_id = self.inter_company_transfer_id.source_warehouse_id.id
        return {'name': 'New', 'type': reverse_type,
                'inter_company_transfer_id': self.inter_company_transfer_id.id,
                "source_warehouse_id": source_warehouse_id, "destination_warehouse_id": destination_warehouse_id,
                'inter_company_transfer_line_ids': [(6, 0, [])]}


class ReverseInterCompanyTransferLines(models.TransientModel):
    """
    For creating reverse inter company transfer lines.
    @author: Maulik Barad.
    """
    _name = "reverse.inter.company.transfer.line.ept"
    _description = "Reverse Inter Company Transfer Lines"

    reverse_ict_id = fields.Many2one("reverse.inter.company.transfer.ept")
    product_id = fields.Many2one('product.product')
    quantity = fields.Float(default=1.0)
    price = fields.Float()
    delivered_qty = fields.Float()
    lot_serial_ids = fields.Many2many("stock.lot", relation="reverse_ict_line_lot_stock_rel", string="Lot/Serial")

    @api.constrains('quantity', 'delivered_qty')
    def _check_quantity(self):
        """
        This method checks if entered quantity is not greater than delivered.
        @author: Maulik Barad.
        """
        for record in self:
            if record.quantity > record.delivered_qty:
                raise UserError(_('You can not enter quantity which was greater than original quantity'))
