# Copyright 2018 Alex Comba - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    production_ids = fields.One2many('mrp.production', 'sale_order_id')
    production_count = fields.Integer(
        compute='_compute_production_count', store=True)

    purchase_ids = fields.Many2many(
        'purchase.order',
        string = 'Purchase Orders',
        compute="_compute_purchase_orders",
    )
    
    @api.depends("production_ids")
    def _compute_production_count(self):
        for sale in self:
            sale.production_count = len(sale.production_ids)

    def action_view_production(self):
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        if self.production_count > 1:
            action['domain'] = [('id', 'in', self.production_ids.ids)]
        else:
            action['views'] = [
                (self.env.ref('mrp.mrp_production_form_view').id, 'form')]
            action['res_id'] = self.production_ids.id
        return action
        
    @api.depends("production_ids")
    def _compute_purchase_count(self):
        for sale in self:
            sale.production_count = len(sale.production_ids)

    def _compute_purchase_orders(self):
        purch_obj = self.env['purchase.order']
        for sale in self:
            sale.purchase_order_ids = [(4, False)]
            #search for purchases that reference the sale
            domain = [('sale_order_id','in',sale.id)]
            domain += [('company_id','=',line.company_id.id)]
            purchase_ids = purchase_obj.search(domain)
            purch_ids = purchase_ids.ids
            sale.purchase_order_ids = [(6, 0, purch_ids)]
            
    def action_view_purchase(self):
        self.ensure_one()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = (
            self.env.ref("purchase.purchase_form_action")
            .with_context(active_id=self.id)
            .read()[0]
        )
        purchases = self.purchase_ids
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
