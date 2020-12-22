from odoo import api, fields, models


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    required_steps = fields.Many2many(comodel_name='mrp.routing.workcenter', string="Previous Steps", relation='mrp_routing_required_steps', column1='required_steps', column2='required_for_steps', copy=False)
    required_for_steps = fields.Many2many(comodel_name='mrp.routing.workcenter', string="Next Steps", relation='mrp_routing_required_steps', column1='required_for_steps', column2='required_steps', copy=False)
