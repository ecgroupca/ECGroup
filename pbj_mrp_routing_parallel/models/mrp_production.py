from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _workorders_create(self, bom, bom_data):
        if bom.routing_id.parallel_steps:
            res = super(MrpProduction, self.with_context(parallel_routing=True))._workorders_create(bom, bom_data)
            for work_order in res:
                if work_order.get_parallel_state() == 'ready':
                    work_order.state = 'ready'
            return res
        return super(MrpProduction, self)._workorders_create(bom, bom_data)
