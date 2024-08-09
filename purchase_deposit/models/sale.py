from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_order_ids = fields.Many2many(
        'purchase.order',
        string = 'Purchase Orders',
        compute="_compute_purchase_orders",
    )
    
    purchase_orders_counted = fields.Integer(
        compute='_compute_purchase_orders_counted', store=True)
        
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
            #purchase_orders = self.env['purchase.order']           
            #for line in purchase_lines:
            #    purchase_orders |= line.order_id           
            sale.purchase_order_ids = [(6, 0, purchases.ids)]
