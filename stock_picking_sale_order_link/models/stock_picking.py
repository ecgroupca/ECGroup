# © 2017 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models,fields


class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    inv_bal_due = fields.Float(
        'Balance Due',
        related='sale_id.inv_bal_due'
        )
    sale_user_id = fields.Many2one('res.users',
        'Responsible',
        related='sale_id.user_id'
        )
    carrier_id = fields.Many2one('delivery.carrier',
        'Carrier',
        related='sale_id.carrier_id'
        )   

    def action_view_sale_order(self):
        """This function returns an action that display existing sales order
        of given picking.
        """
        self.ensure_one()
        return self.sale_id.get_formview_action()
