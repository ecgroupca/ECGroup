from odoo import api, fields, models

  
class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    """acknowledged = fields.Boolean('Acknowledged',track_visibility='onchange')
    shipped = fields.Boolean('Shipped',track_visibility='onchange')
    received = fields.Boolean('Received',track_visibility='onchange')
    late order = fields.Boolean('Late Order',track_visibility='onchange')"""
    
    approval_id = fields.Many2one(
        'purchase.approval',
        'Approval', 
        )