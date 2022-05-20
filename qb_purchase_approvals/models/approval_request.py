from odoo import api, fields, models

  
class ApprovalRequest(models.Model):
    _inherit = "approval.request"
    
    purchase_order_ids = fields.Many2many(
        'purchase.order',
        string='Purchase Orders',
        compute = '_compute_purchase_orders',
    )
    
    request_status = fields.Selection([
        ('new', 'To Submit'),
        ('pending', 'Submitted'),
        ('approved', 'Approved'),
        ('rfqs', 'RFQs Created'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel')],
        )
        
    def _compute_purchase_orders(self):
        for approval in self:
            domain = [('approval_request_id','=',approval.id)]
            prod_lines = self.env['approval.product.line'].search(domain)
            purchase_orders = []
            approval.purchase_order_ids = [(4, False)]
            for line in prod_lines: 
                purch_id = line.purchase_order_line_id.order_id.id            
                if purch_id not in purchase_orders:
                    purchase_orders.append(purch_id)
                    approval.purchase_order_ids = [(4, purch_id)]
            if approval.purchase_order_count > 0 and approval.request_status == 'approved': 
                approval.request_status = 'rfqs'                        
        
         