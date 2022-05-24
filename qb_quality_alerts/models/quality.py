from odoo import api, fields, models

  
class QualityAlert(models.Model):
    _inherit = "quality.alert"
    
    mrp_ids = fields.Many2many(
        'mrp.production',
        string = 'Production Orders',
    )
    
    mrp_count = fields.Integer(
        string="MRP Count", compute="_compute_doc_counts",
    )
    
    approval_ids = fields.Many2many(
        'approval.request',
        string = 'Approval Requests',
    )

    approval_count = fields.Integer(
        string="Approval Count", compute="_compute_doc_counts",
    )
    
    purchase_ids = fields.Many2many(
        'purchase.order',
        string = 'Purchase Orders',
    )

    purchase_count = fields.Integer(
        string="Purchase Count", compute="_compute_doc_counts",
    )
    
    def _compute_doc_counts(self):
        for quality in self:
            quality.mrp_count = len(quality.mrp_ids)
            quality.approval_count = len(quality.approval_ids)
            quality.purchase_count = len(quality.purchase_ids)
            
                