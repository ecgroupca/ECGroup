from odoo import api, fields, models

  
class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    quality_alert_ids = fields.Many2many(
        'quality.alert',
        string = 'Quality Alerts',
        compute = '_compute_quality_alerts',
    )
    
    quality_count = fields.Integer(
        string="Quality Alerts Count", compute="_compute_quality_alerts",
    )
    
    def _compute_quality_alerts(self):
        quality_obj = self.env['quality.alert']
        for purchase in self:
            purchase.quality_alert_ids = [(4, False)]
            #search for products that have quality
            quality_ids = []
            for line in purchase.order_line:
                domain = [('product_id','=',line.product_id.id)]
                qual_ids = quality_obj.search(domain)
                #for qual in qual_ids:
                #    qual.purchase_ids = [(4, purchase.id)]
                quality_ids += qual_ids.ids
            purchase.quality_alert_ids = [(6, 0, quality_ids)]
            purchase.quality_count = len(quality_ids)
            
    def action_view_quality(self):
        self.ensure_one()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = (
            self.env.ref("quality_control.quality_alert_action_check")
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
                                
                    
                