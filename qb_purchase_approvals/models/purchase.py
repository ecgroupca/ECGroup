from odoo import api, fields, models

  
class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    approval_id = fields.Many2one(
        'approval.request',
        'Approval', 
        )