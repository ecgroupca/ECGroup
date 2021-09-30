from odoo import api, fields, models

class MRPWorkorder(models.Model):
    _inherit = "mrp.workorder"
    
    next_wo_id = fields.Many2one(
        'Next Workorder',
        compute = '_get_next_wo',
        )
        
    @api.depends('production_id')
    def _get_next_wo(self):
        for wo in self:
            #prod_id = wo.production_id
            #routing_id = prod_id.routing_id
            wo.next_wo_id = False
            for next_wo in wo.next_work_order_ids:
                wo.next_wo_id = next_wo
                break
            if not wo.next_wo_id:
                #then we have to lookup the 
            