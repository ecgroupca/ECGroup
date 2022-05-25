from odoo import api, fields, models

  
class MRPProduction(models.Model):
    _inherit = "mrp.production"
    
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
        for mrp in self:
            mrp.quality_alert_ids = [(4, False)]
            #search for products that have quality
            quality_ids = []
            move_line_ids = mrp.move_raw_ids
            for line in move_line_ids:
                domain = [('product_id','=',line.product_id.id)]
                domain += [('company_id','=',line.company_id.id)]
                qual_ids = quality_obj.search(domain)
                quality_ids += qual_ids.ids
            domain = [('product_id','=',mrp.product_id.id)]
            domain += [('company_id','=',line.company_id.id)]
            mrp_prod_qual_id = quality_obj.search(domain)
            if mrp_prod_qual_id:
                quality_ids += mrp_prod_qual_id.ids
            mrp.quality_alert_ids = [(6, 0, quality_ids)]
            mrp.quality_count = len(quality_ids)

            
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
