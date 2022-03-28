"""
For inter_company_transfer_ept module.
"""
from odoo import fields, api, models


class Picking(models.Model):
    """
    Inherited for adding relation with inter company transfer.
    @author: Maulik Barad on Date 25-Sep-2019.
    """
    _inherit = 'stock.picking'

    inter_company_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT",
                                                copy=False, help="Reference of ICT.")

    def _create_backorder(self):
        """
        Inherited for adding ICT relation to backorder also.
        @author: Maulik Barad on Date 09-Oct-2019.
        """
        res = super(Picking, self)._create_backorder()
        for backorder in res:
            if backorder.backorder_id and backorder.backorder_id.inter_company_transfer_id:
                backorder.write({"inter_company_transfer_id":backorder.backorder_id.\
                                 inter_company_transfer_id.id})
        return res
        
    def action_done(self):
        res = super().action_done()
        for pick in self:
            if pick.inter_company_transfer_id:
                ict_done = True
                for trans in pick.inter_company_transfer_id.picking_ids:
                    if trans.state != 'done':
                        ict_done = False
                if ict_done:
                    pick.inter_company_transfer_id.state = 'transferred'
        return res
