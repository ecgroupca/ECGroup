# -*- coding: utf-8 -*-
"""
For inter_company_transfer_ept module.
"""
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class ReverseInterCompanyTransfer(models.TransientModel):
    """
    For creating reverse inter company transfer.
    @author: Maulik Barad on Date 25-Sep-2019.
    """
    _name = 'reverse.inter.company.transfer.ept'
    _description = 'Reverse Inter Company Transfer'

    inter_company_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT")
    reverse_ict_line_ids = fields.One2many('reverse.inter.company.transfer.line.ept',
                                           'reverse_ict_id')

    def action_create_reverse_process(self):
        """
        It creates reverse inter company transfer.
        @author: Maulik Barad on Date 25-Sep-2019.
        """
        reverse_inter_company_transfer_id = self.inter_company_transfer_id.copy(default={
            'type':'ict_reverse', 'inter_company_transfer_id':self.inter_company_transfer_id.id,
            'name':'New', 'inter_company_transfer_line_ids':[(6, 0, [])]})

        for line in self.reverse_ict_line_ids:
            self.env['inter.company.transfer.line.ept'].create({
                'inter_company_transfer_id':reverse_inter_company_transfer_id.id,
                'product_id':line.product_id.id,
                'quantity':line.quantity or 1,
                'price':line.price
                })
        # Added by Udit on 18th December 2019
        if reverse_inter_company_transfer_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'inter.company.transfer.ept',
                'views': [(False, 'tree'),(False, 'form')],
                'domain': [('id', '=', reverse_inter_company_transfer_id.id)],
                'name': 'Reverse ICTs',
                # 'context': {'default_inter_company_transfer_id': self.id,
                #             'default_reverse_ict_line_ids': [(6, 0, created_reverse_line_ids)]},
                'target': 'current',
            }

        return False


class ReverseInterCompanyTransferLines(models.TransientModel):
    """
    For creating reverse inter company transfer lines.
    @author: Maulik Barad on Date 25-Sep-2019.
    """
    _name = "reverse.inter.company.transfer.line.ept"
    _description = "Reverse Inter Company Transfer Lines"

    reverse_ict_id = fields.Many2one("reverse.inter.company.transfer.ept")
    product_id = fields.Many2one('product.product')
    quantity = fields.Float(default=1.0)
    price = fields.Float()
    delivered_qty = fields.Float()

    @api.constrains('quantity', 'delivered_qty')
    def _check_quantity(self):
        """
        This method checks if entered quantity is not greater than delivered.
        @author: Maulik Barad on Date 25-Sep-2019.
        """
        if self.quantity > self.delivered_qty:
            raise Warning(_('You can not enter quantity which was greater than original quantity'))
