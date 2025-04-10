from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    taxes = fields.Many2many("account.tax",string="Sales Taxes")
    
    @api.onchange('taxes')
    def _onchange_taxes(self):   
        for sale in self:
            header_taxes = sale.taxes and sale.taxes.ids or []
            if header_taxes:
                for line in sale.order_line:
                    product = line.product_id
                    if product.default_code != 'Freight':
                        line.tax_id = [(6, 0, header_taxes)]