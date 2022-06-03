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
        ('rfqs', 'Form Created'),
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
                purchase = line.purchase_order_line_id\
                   and line.purchase_order_line_id.order_id or None
                purch_id = purchase and purchase.id or 0        
                if purch_id and purch_id not in purchase_orders:
                    purchase_orders.append(purch_id)
                    approval.purchase_order_ids = [(4, purch_id)]
                    purchase.approval_id = approval                
            if approval.purchase_order_count > 0\
                and approval.request_status == 'approved': 
                approval.request_status = 'rfqs'