from odoo import api, fields, models
    
  
class QualityAlert(models.Model):
    _inherit = "quality.alert"
    
    manufacturing_order_id = fields.Many2one(
        'mrp.production',
        string = 'Manufacturing Order',      
    )
    
    mrp_count = fields.Integer(
        string="MRP Count", 
        compute="_compute_doc_counts",
    )
    
    approval_ids = fields.Many2many(
        'approval.request',
        string = 'Approval Requests',
        compute="_compute_related_docs",
    )

    approval_count = fields.Integer(
        string="Approval Count", 
        compute="_compute_doc_counts",
    )
    
    purchase_ids = fields.Many2many(
        'purchase.order',
        string = 'Purchase Orders',
        compute="_compute_related_docs",
    )

    purchase_count = fields.Integer(
        string="Purchase Count", 
        compute="_compute_doc_counts",
    )
    
    def _compute_related_docs(self):
        for quality in self:
            stock_move_obj = self.env['stock.move']
            purch_line_obj = self.env['purchase.order.line']
            appro_line_obj = self.env['approval.product.line']
            main_domain = [('product_id','=',quality.product_id.id)]
            main_domain += [('company_id','=',quality.company_id.id)]
            
            #purchases that have quality alerts
            purchase_lines = purch_line_obj.search(main_domain)
            purchase_orders = self.env['purchase.order']           
            for line in purchase_lines:
                purchase_orders |= line.order_id           
            quality.purchase_ids = [(6, 0, purchase_orders.ids)]
            
            #approvals that have quality alerts
            approval_lines = appro_line_obj.search(main_domain)
            approvals = self.env['approval.request']            
            for line in approval_lines:
                approvals |= line.approval_request_id         
            quality.approval_ids = [(6, 0, approvals.ids)]
            
    def _compute_doc_counts(self):
        for quality in self:
            quality.mrp_count = quality.manufacturing_order_id and 1 or 0
            quality.approval_count = len(quality.approval_ids)
            quality.purchase_count = len(quality.purchase_ids)
            
    def action_view_mrp(self):
        self.ensure_one()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = (
            self.env.ref("mrp.mrp_production_action")
            .with_context(active_id=self.id)
            .read()[0]
        )
        mrp_orders = self.manufacturing_order_id
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

    def action_view_approval(self):
        self.ensure_one()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = (
            self.env.ref("approvals.approval_request_action_all")
            .with_context(active_id=self.id)
            .read()[0]
        )
        approvals = self.approval_ids
        if len(approvals) > 1:
            action["domain"] = [("id", "in", approvals.ids)]
        elif approvals:
            action.update(
                res_id=approvals.id, 
                view_mode="form", 
                view_id=False, 
                views=False,
            )
        return action        