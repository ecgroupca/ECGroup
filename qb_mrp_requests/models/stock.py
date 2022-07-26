from odoo import api, fields, models

  
class StockPicking(models.Model):
    _inherit = "stock.picking"

    operation_id = fields.Many2one(
        'mrp.routing.workcenter',
        tracking=True,
        ) 
