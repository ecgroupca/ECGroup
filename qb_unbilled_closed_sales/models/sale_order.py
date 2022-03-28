from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    trans_shipped_date = fields.Datetime(
        store = True,
        )
                    
                        
                
            
        
         