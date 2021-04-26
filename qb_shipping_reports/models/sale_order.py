from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    sidemark = fields.Char("Sidemark")