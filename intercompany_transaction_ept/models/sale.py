"""
For inter_company_transfer_ept module.
"""
from odoo import fields, models


class SaleOrder(models.Model):
    """
    Inherited for adding relation with inter company transfer.
    @author: Maulik Barad on Date 24-Sep-2019.
    """
    _inherit = 'sale.order'

    inter_company_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT",
                                                copy=False, help="Reference of ICT.")

    def _prepare_invoice(self):
        """
        Inherited for adding relation with ICT if created by it.
        @author: Maulik Barad on Date 16-Oct-2019.
        @return: Dictionary for creating invoice.
        """
        vals = super(SaleOrder, self)._prepare_invoice()
        if self.inter_company_transfer_id:
            vals.update({
                'inter_company_transfer_id':self.inter_company_transfer_id.id
            })
        return vals
