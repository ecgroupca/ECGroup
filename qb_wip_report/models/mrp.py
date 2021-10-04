from odoo import api, fields, models

class MRPWorkorder(models.Model):
    _inherit = "mrp.workorder"
    
    next_wo_id = fields.Many2one(
        'mrp.workorder',
        string = 'Next Workorder',
        compute = '_get_next_wo',
        )
        
    @api.depends('production_id')
    def _get_next_wo(self):
        for wo in self:
            prod_id = wo.production_id
            domain = [('production_id','=',prod_id.id),('id','=',wo.id + 1)]
            next_wo = wo.search(domain, order='id asc')
            wo.next_wo_id = next_wo and next_wo.id or False           
            