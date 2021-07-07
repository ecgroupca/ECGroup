from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    received = fields.Boolean("Received", compute="_compute_open_shipments")
    open_shipment = fields.Boolean("Open Shipments",compute="_compute_open_shipments")
    open_production = fields.Boolean("Open Shipments",compute="_compute_open_shipments")
    needs_drawing = fields.Boolean("Needs Drawing")
    needs_sample_approval = fields.Boolean("Needs Sample Approval")
    
    @api.depends('order_line','production_ids','picking_ids','state')
    def _compute_open_shipments(self):
        for sale in self:
            #1. mark the order as received if it has been confirmed.
            if sale.state not in ['draft','cancel']:
                sale.received = True
        #2. open_shipment if there are any undelivered items on the SO.
        for line in sale.order_line:
          if line.qty_delivered < line.product_uom_qty:
            sale.open_shipment = True
            break
        #3. open production if there are any mrp.prods that are not done.
        for mrp in sale.production_ids:
            if mrp.state not in ['done','cancel']:
                sale.open_production = True
            
        
         