from odoo import api, fields, models

  
class ApprovalRequest(models.Model):
    _inherit = "approval.request"
    
    purchase_order_ids = fields.Many2many(
        'purchase.order',
        string='purchase Orders',
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
            for line in prod_lines: 
                purch_id = line.purchase_order_line_id.order_id.id            
                if purch_id not in purchase_orders:
                    purchase_orders.append(purch_id)
                    approval.purchase_order_ids = [(4, purch_id)]
            if purchase_orders and approval.request_status == 'approved':
                approval.request_status = 'rfqs'
                for approver in approval.approver_ids:
                    if approver.status == 'approved':
                        approver.status = 'rfqs'                    
                    
    @api.depends('approver_ids.status')
    def _compute_request_status(self):
        for request in self:
            status_lst = request.mapped('approver_ids.status')
            minimal_approver = request.approval_minimum if len(status_lst) >= request.approval_minimum else len(status_lst)
            if status_lst:
                if status_lst.count('cancel'):
                    status = 'cancel'
                elif status_lst.count('refused'):
                    status = 'refused'
                elif status_lst.count('new'):
                    status = 'new'
                elif status_lst.count('approved') >= minimal_approver:
                    status = 'approved'
                elif status_lst.count('rfqs'):
                    status = 'rfqs'
                else:
                    status = 'pending'
            else:
                status = 'new'
            request.request_status = status
            
class ApprovalApprover(models.Model):
    _inherit = 'approval.approver'

    status = fields.Selection([
        ('new', 'New'),
        ('pending', 'To Approve'),
        ('approved', 'Approved'),
        ('rfqs', 'RFQs Created'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel')]
    
    
                        
                
            
        
         