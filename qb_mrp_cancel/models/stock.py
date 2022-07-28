from odoo import api, fields, models

  
class StockPicking(models.Model):
    _inherit = "stock.picking"

    workorder_id = fields.Many2one(
        'mrp.workorder',
        string = 'Workorder',
        tracking=True,
        )