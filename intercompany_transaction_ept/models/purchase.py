"""
For inter_company_transfer_ept module.
"""
from odoo import fields, models, api


class PurchaseOrder(models.Model):
    """
    Inherited for adding relation with inter company transfer.
    @author: Maulik Barad on Date 24-Sep-2019.
    """
    _inherit = 'purchase.order'
    _description = 'Purchase Order'

    inter_company_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT",
                                                copy=False, help="Reference of ICT.")

    @api.model
    def _prepare_picking(self):
        """
        Inherited for adding relation with ICT if created by it.
        @author: Maulik Barad on Date 16-Oct-2019.
        @return: Dictionary for creating picking.
        """
        vals = super(PurchaseOrder, self)._prepare_picking()
        if self.inter_company_transfer_id:
            vals.update({
                'inter_company_transfer_id':self.inter_company_transfer_id.id
            })
        return vals

    def action_view_invoice(self):
        """
        Inherited for adding relation with ICT if created by it.
        @author: Maulik Barad on Date 16-Oct-2019.
        @return: Action for displaying vendor bill for purchase order.
        """
        action = super(PurchaseOrder, self).action_view_invoice()
        if self.env.context.get('create_bill', False) and self.inter_company_transfer_id:
            action['context']['default_inter_company_transfer_id'] = self.inter_company_transfer_id.id
        return action
