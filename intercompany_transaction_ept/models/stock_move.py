"""
For inter_company_transfer_ept module.
"""
from odoo import models


class StockMove(models.Model):
    """
    Inherited for passing values to picking.
    @author: Maulik Barad on Date 16-Oct-2019.
    """
    _inherit = "stock.move"

    def _get_new_picking_values(self):
        """
        Inherited for adding relation with ICT if created by it.
        @author: Maulik Barad on Date 16-Oct-2019.
        @return: Dictionary for creating picking.
        """
        vals = super(StockMove, self)._get_new_picking_values()
        if self.sale_line_id.order_id.inter_company_transfer_id:
            vals.update({
                'inter_company_transfer_id':self.sale_line_id.order_id.inter_company_transfer_id.id
                })
        return vals
