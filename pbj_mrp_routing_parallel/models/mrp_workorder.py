from odoo import api, fields, models
from odoo.tools import float_compare


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    next_work_order_ids = fields.Many2many(string="Next Work Orders", comodel_name='mrp.workorder', compute='_compute_work_orders')
    previous_work_order_ids = fields.Many2many(string="Previous Work Orders", comodel_name='mrp.workorder', compute='_compute_work_orders')

    def _compute_work_orders(self):
        for rec in self:
            rec.next_work_order_ids = self.get_next_work_orders()
            rec.previous_work_order_ids = self.get_previous_work_orders()

    def get_next_work_orders(self):
        operations = self.env['mrp.routing.workcenter'].search([('required_steps', 'in', self.operation_id.id)])
        return self.search([('operation_id', 'in', operations.ids), ('production_id', '=', self.production_id.id)])

    def get_previous_work_orders(self):
        operations = self.env['mrp.routing.workcenter'].search([('required_for_steps', 'in', self.operation_id.id)])
        return self.search([('operation_id', 'in', operations.ids), ('production_id', '=', self.production_id.id)])

    def get_parallel_state(self):
        rounding = self.product_id.uom_id.rounding
        if self.state in ['progress', 'done', 'cancel']:
            return self.state
        previous_work_orders = self.get_previous_work_orders()
        if not previous_work_orders:
            return 'ready'
        for work_order in previous_work_orders:
            if work_order.operation_id.batch == 'yes':
                if float_compare(work_order.qty_produced, 0, rounding) <= 0:
                    return 'pending'
            elif float_compare(work_order.qty_produced, work_order.production_id.product_qty, rounding) < 0:
                return 'pending'
        return 'ready'

    def _start_nextworkorder(self):
        if self.operation_id.routing_id.parallel_steps:
            for work_order in self.next_work_order_ids:
                if work_order.state == 'pending' and work_order.get_parallel_state() == 'ready':
                    work_order.state = 'ready'
        else:
            return super(MrpWorkorder, self)._start_nextworkorder()

    @api.onchange('finished_lot_id')
    def _onchange_finished_lot_id(self):
        if self.operation_id.routing_id.parallel_steps:
            # Since our routing is no longer linear, just check all steps for a matching lot
            for work_order in self.production_id.workorder_ids:
                line = work_order.finished_workorder_line_ids.filtered(lambda line: line.product_id == self.product_id and line.lot_id == self.finished_lot_id)
                if line:
                    self.qty_producing = line.qty_done
                    return
        else:
            return super(MrpWorkorder, self)._onchange_finished_lot_id()

    @api.model
    def create(self, vals):
        if 'parallel_routing' in self.env.context:
            vals['state'] = 'pending'
        return super(MrpWorkorder, self).create(vals)

    def write(self, vals):
        if 'parallel_routing' in self.env.context and 'next_work_order_id' in vals:
            del vals['next_work_order_id']
        return super(MrpWorkorder, self).write(vals)
