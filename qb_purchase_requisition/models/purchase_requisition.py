from odoo import api, fields, models


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"
    
    
    def action_create_rfqs(self):
        for req in self:
            #loop through the req lines and aggregate vendors creating a new PO for each one
            
    
        
class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisition.line"
    
    
    vendor_id = fields.Many2one('res.partner', 
        string="Vendor", 
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
        )
   
   
                                
                    
                