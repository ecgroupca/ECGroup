# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api


class Picking(models.Model):
    """
    Inherited for adding relation with inter company transfer.
    @author: Maulik Barad.
    """
    _inherit = 'stock.picking'

    inter_company_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT", copy=False,
                                                help="Reference of ICT.")

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """
        Inherited method for setting the reverse ict, while creating the return picking.
        @author: Maulik Barad on Date 23-Feb-2021.
        """
        if isinstance(default, dict) and self._context.get("default_ict"):
            default.update({"inter_company_transfer_id": self._context.get("default_ict")})

        return super(Picking, self).copy(default)

    def _create_backorder(self):
        """
        Inherited for adding ICT relation to backorder also.
        @author: Maulik Barad.
        @updates: Adam O'Connor
        """
        res = super(Picking, self)._create_backorder()
        for backorder in res:
            if backorder.backorder_id and backorder.backorder_id.inter_company_transfer_id:
                backorder.write({"inter_company_transfer_id": backorder.backorder_id.inter_company_transfer_id.id})
        return res
        
    def action_done(self):
        """
        Inherited for assigning transferred state
        @updates: Adam O'Connor
        """
        res = super().action_done()
        for pick in self:
            if pick.inter_company_transfer_id:
                ict_done = True
                #ideal - only count backorders if the item on them is 
                #not canceled
                for trans in pick.inter_company_transfer_id.picking_ids:
                    if trans.state not in ['done','cancel']:
                        ict_done = False
                if ict_done:
                    pick.inter_company_transfer_id.state = 'transferred'
        return res
