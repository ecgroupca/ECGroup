from odoo import api, fields, models


class MrpAbstractWorkorder(models.AbstractModel):
    _inherit = 'mrp.abstract.workorder'

    def _update_finished_move(self):
        if isinstance(self, type(self.env['mrp.workorder'])) and self.operation_id.routing_id.parallel_steps:
            if any([wo != self and wo.state != 'done' for wo in self.production_id.workorder_ids]):
                return
        return super(MrpAbstractWorkorder, self)._update_finished_move()
