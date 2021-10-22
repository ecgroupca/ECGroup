from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    needs_ten_ninety_nine = fields.Boolean("Needs 1099")
                           
                
            
        
         