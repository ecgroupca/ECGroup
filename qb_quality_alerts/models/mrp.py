from odoo import api, fields, models

  
class MRPProduction(models.Model):
    _inherit = "mrp.production"
    
    quality_alert_ids = fields.One2many(
        'quality.alert', 
        "production_id", 
        string="Alerts"
        compute='_compute_quality_alerts'
        )
    quality_alert_count = fields.Integer(compute='_compute_quality_alert_count')

    def _compute_quality_alert_count(self):
        for production in self:
            production.quality_alert_count = len(production.quality_alert_ids)
            
    def _compute_quality_alerts(self):
        for production in self:
            #find all alerts that have manufacturing_order_id = production
            domain = [('manufacturing_order_id','=',production.id)]
            production.quality_alert_ids = self.env['quality.alert'].search(domain)
