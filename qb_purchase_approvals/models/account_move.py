from odoo import api, fields, models

  
class AccountMove(models.Model):
    _inherit = "account.move"
    
    approval_id = fields.Many2one(
        'approval.request',
        'Approval', 
        )