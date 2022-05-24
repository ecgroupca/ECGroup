from odoo import api, fields, models

  
class ApprovalRequest(models.Model):
    _inherit = "approval.request"
    
    quality_alert_ids = fields.Many2many(
        'purchase.order',
        string = 'Purchase Orders',
        compute = '_compute_quality_alerts',
    )
    
    quality_count = fields.Integer(
        string="Quality Alerts Count", compute="_compute_quality_alerts",
    )
    
    def _compute_quality_alerts(self):
        quality_obj = self.env['quality.alert']
        for approval in self:
            approval.quality_alert_ids = [(4, False)]
            #search for products that have quality
            quality_ids = []
            for line in approval.product_line_ids:
                domain = ['|',('product_id','=',line.product_id.id),('product_id','=',line.product_id.id)]
                qual_ids = quality_obj.search(domain)
                for qual in qual_ids:
                    qual.approval_ids = [(4, [approval.id])]
                quality_ids.append(qual_ids.ids)
            approval.quality_alert_ids = [(4, quality_ids)]
            approval.quality_count = len(quality_ids)
            
    def action_view_quality(self):
        self.ensure_one()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = (
            self.env.ref("quality_control.quality_check_action_main")
            .with_context(active_id=self.id)
            .read()[0]
        )
        alerts = self.quality_alert_ids
        if len(alerts) > 1:
            action["domain"] = [("id", "in", alerts.ids)]
        elif alerts:
            action.update(
                res_id=alerts.id, view_mode="form", view_id=False, views=False,
            )
        return action
         