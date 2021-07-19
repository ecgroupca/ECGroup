from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    shipped_date = fields.Datetime(related="picking_id.date_done")
    sale_id = fields.Many2one(related="picking_id.sale_id")
    sidemark = fields.Char(related="sale_id.sidemark")
    client_id = fields.Many2one(related="sale_id.partner_id")
    carrier_id = fields.Many2one(related="picking_id.carrier_id")
    product_default_code = fields.Char(related="product_id.default_code")
    bill_of_lading = fields.Char(related="picking_id.sale_id.name")
    
    