from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_order_ids = fields.Many2many(
        'purchase.order',
        string = 'Purchase Orders',
        compute="_compute_purchase_orders",
    )
    
    purchase_orders_counted = fields.Integer(
        compute='_compute_purchase_orders_counted')
        
    @api.depends("purchase_order_ids")
    def _compute_purchase_orders_counted(self):
        for sale in self:
            sale.purchase_orders_counted = len(sale.purchase_order_ids)

    def _compute_purchase_orders(self):
        purch_obj = self.env['purchase.order']
        for sale in self:
            sale.purchase_order_ids = [(4, False)]
            #search for purchases that reference the sale
            #purchases that have quality alerts
            main_domain = [('sale_order_id','in',[sale.id])]
            purchases = purch_obj.search(main_domain)         
            sale.purchase_order_ids = [(6, 0, purchases.ids)]
            
    def action_view_purchases(self):
        self.ensure_one()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = (
            self.env.ref("purchase.purchase_form_action")
            .with_context(active_id=self.id)
            .read()[0]
        )
        purchases = self.purchase_order_ids
        if len(purchases) > 1:
            action["domain"] = [("id", "in", purchases.ids)]
        elif purchases:
            action.update(
                res_id=purchases.id, 
                view_mode="form", 
                view_id=False,
                views=False,
            )
        return action
