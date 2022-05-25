from odoo import api, fields, models
    
  
class QualityAlert(models.Model):
    _inherit = "quality.alert"
    
    mrp_ids = fields.Many2many(
        'mrp.production',
        string = 'Production Orders',
    )
    
    mrp_count = fields.Integer(
        string="MRP Count", 
        compute="_compute_doc_counts",
    )
    
    approval_ids = fields.Many2many(
        'approval.request',
        string = 'Approval Requests',
    )

    approval_count = fields.Integer(
        string="Approval Count", 
        compute="_compute_doc_counts",
    )
    
    purchase_ids = fields.Many2many(
        'purchase.order',
        string = 'Purchase Orders',
    )

    purchase_count = fields.Integer(
        string="Purchase Count", 
        compute="_compute_doc_counts",
    )
        
    def _compute_doc_counts(self):
        for quality in self:
            quality.mrp_count = len(quality.mrp_ids)
            quality.approval_count = len(quality.approval_ids)
            quality.purchase_count = len(quality.purchase_ids)
            
    def action_view_mrp(self):
        self.ensure_one()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = (
            self.env.ref("mrp.action_mrp_production_form")
            .with_context(active_id=self.id)
            .read()[0]
        )
        mrp_orders = self.mrp_ids
        if len(mrp_orders) > 1:
            action["domain"] = [("id", "in", mrp_orders.ids)]
        elif mrp_orders:
            action.update(
                res_id=mrp_orders.id, view_mode="form", view_id=False, views=False,
            )
        return action

    def action_view_purchase(self):
        self.ensure_one()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = (
            self.env.ref("purchase.purchase_rfq")
            .with_context(active_id=self.id)
            .read()[0]
        )
        purchases = self.purchase_ids
        if len(purchases) > 1:
            action["domain"] = [("id", "in", purchases.ids)]
        elif purchases:
            action.update(
                res_id=purchases.id, view_mode="form", view_id=False, views=False,
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
                res_id=approvals.id, view_mode="form", view_id=False, views=False,
            )
        return action        