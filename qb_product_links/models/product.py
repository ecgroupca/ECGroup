from odoo import api, fields, models

  
class ProductTemplate(models.Model):
    _inherit = "product.template"

    mrp_count = fields.Integer('# MOs',
        compute='_compute_mrp_count', compute_sudo=False)

    mrp_order_ids = fields.One2many('mrp.production',
        string = 'MOs',
        compute='_compute_mrp_orders', compute_sudo=False)
        
    purchase_ids = fields.Many2many(
        'purchase.order',
        string = 'Purchase Orders',
        compute="_compute_purchases",
    )

    purchase_count = fields.Integer(
        string="Purchase Count", 
        compute="_compute_purchase_counts",
    )

    def _compute_mrp_count(self):
        for product in self:
            product.mrp_count = len(product.mrp_order_ids)
            
    def _compute_mrp_orders(self):
        for tmpl in self:
            domain = ['|',('product_id.product_tmpl_id', '=', tmpl.id)]
            domain += [('move_raw_ids.product_id.product_tmpl_id','in',[tmpl.id])]
            domain += [('state','!=','cancel')]
            mrp_ids = self.env['mrp.production'].search(domain)
            self.mrp_order_ids = [(6,0,mrp_ids.ids)]

    def action_view_mrp(self):
        self.ensure_one()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = (
            self.env.ref("mrp.mrp_production_action")
            .with_context(active_id=self.id)
            .read()[0]
        )
        mrp_orders = self.mrp_order_ids
        if len(mrp_orders) > 1:
            action["domain"] = [("id", "in", mrp_orders.ids)]
        elif mrp_orders:
            action.update(
                res_id=mrp_orders.id, 
                view_mode="form", 
                view_id=False, 
                views=False,
            )
        return action  

    def _compute_purchase_counts(self):
        for tmpl in self:
            tmpl.purchase_count = len(tmpl.purchase_ids)        

    def _compute_purchases(self):
        for tmpl in self:
            domain = [('state', '!=', 'cancel'),('order_line.product_id.product_tmpl_id','in',[tmpl.id])]
            purch_ids = self.env['purchase.order'].search(domain)
            tmpl.purchase_ids = [(6,0,purch_ids.ids)]
            
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
        
            
class ProductProduct(models.Model):
    _inherit = "product.product"

    mrp_count = fields.Integer('# MOs',
        compute='_compute_mrp_count', compute_sudo=False)
    mrp_order_ids = fields.One2many('mrp.production',
        string = 'MOs',
        compute='_compute_mrp_orders', compute_sudo=False)
        
    purchase_ids = fields.Many2many(
        'purchase.order',
        string = 'Purchase Orders',
        compute="_compute_purchases",
    )

    purchase_count = fields.Integer(
        string="Purchase Count", 
        compute="_compute_purchase_counts",
    )
    
    def _compute_mrp_count(self):
        for product in self:
            product.mrp_count = len(product.mrp_order_ids)

    def _compute_mrp_orders(self):
        for product in self:
            domain = ['|',('product_id', '=', product.id)]
            domain += [('move_raw_ids.product_id','in',[product.id])]
            domain += [('state','!=','cancel')]
            mrp_ids = self.env['mrp.production'].search(domain)
            self.mrp_order_ids = [(6,0,mrp_ids.ids)]
            
    def action_view_mrp(self):
        self.ensure_one()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = (
            self.env.ref("mrp.mrp_production_action")
            .with_context(active_id=self.id)
            .read()[0]
        )
        mrp_orders = self.mrp_order_ids
        if len(mrp_orders) > 1:
            action["domain"] = [("id", "in", mrp_orders.ids)]
        elif mrp_orders:
            action.update(
                res_id=mrp_orders.id,
                view_mode="form", 
                view_id=False, 
                views=False,
            )
        return action
        
    def _compute_purchase_counts(self):
        for product in self:
            product.purchase_count = len(product.purchase_ids)        

    def _compute_purchases(self):
        for product in self:
            domain = [('state', '!=', 'cancel'),('order_line.product_id','in',[product.id])]
            purch_ids = self.env['purchase.order'].search(domain)
            product.purchase_ids = [(6,0,purch_ids.ids)]
            
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