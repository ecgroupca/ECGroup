# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class SaleOrder(models.Model):
    """
    Inherited for adding relation with inter company transfer.
    @author: Maulik Barad.
    """
    _inherit = 'sale.order'

    inter_company_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT",
                                                copy=False, help="Reference of ICT.")

    def _prepare_invoice(self):
        """
        Inherited for adding relation with ICT if created by it.
        @author: Maulik Barad.
        @return: Dictionary for creating invoice.
        """
        vals = super(SaleOrder, self)._prepare_invoice()
        if self.inter_company_transfer_id:
            ict = self.inter_company_transfer_id
            vals.update({'inter_company_transfer_id': ict.id})
            if ict.source_company_id.sale_journal_id:
                vals.update({'journal_id': ict.source_company_id.sale_journal_id.id})
        return vals
