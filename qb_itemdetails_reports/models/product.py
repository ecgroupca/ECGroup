from odoo import api, fields, models

  
class ProductProduct(models.Model):
    _inherit = "product.product"
    
    reserved_order_ids = fields.Many2many(
        'reserved.order',
        string='Reserved Orders',
        compute = '_compute_reserved_orders',
    )
    
    def _compute_reserved_orders(self):
        for prod in self:
            prod.reserved_order_ids = [(4, False)] 
            res_line_ids = prod.reserved_line_ids
            orders = {}
            for line in res_line_ids:           
                trans = line.move_id.raw_material_production_id or line.picking_id or None
                pick_type = trans and trans.picking_type_id or None
                if pick_type and pick_type.code in ['mrp_operation','outgoing','internal']:
                    if line.state not in ['cancel']:
                        if trans and trans.name in orders:
                            orders[trans.id] = trans.name 
                        else:
                            vals = {
                                'product_id': prod.id,
                                'move_line_id': line.id,                      
                                'product_uom_qty': line.product_uom_qty,                        
                                'name': trans and trans.name or 'No order',                            
                            }
                            reserved_order = self.env['reserved.order'].sudo().create(vals)
                            prod.reserved_order_ids = [(4, reserved_order.id)]  
    
    
                        
                
            
        
         