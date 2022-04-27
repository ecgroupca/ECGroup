from odoo import api, fields, models

class SaleOrderTags(models.Model):
    _name = 'order.tags'
    _description = 'Order Tags'
    
    name = fields.Char('Name')
    sale_id = fields.Many2one('sale.order',string = 'Sale')    
    

class CRMTeam(models.Model):
    _inherit = "crm.team"
    
    sales_rep_ids = fields.Many2many('res.partner', string='Sales Reps', help='Sales Representatives for the showroom.')
    
class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    received = fields.Boolean("Received", compute="_compute_open_shipments", store=True)
    open_shipment = fields.Boolean("Open Shipments",compute="_compute_open_shipments", store=True)
    open_production = fields.Boolean("Open Production",compute="_compute_open_shipments", store=True)
    needs_drawing = fields.Boolean("Needs Drawing")
    needs_sample_approval = fields.Boolean("Needs Sample Approval")
    sales_rep_ids = fields.Many2many('res.partner', 
        related='team_id.sales_rep_ids')
    sales_rep_id = fields.Many2one('res.partner', 
        'Sales Rep.', 
        domain="[('id','in',sales_rep_ids)]",
        help='Sales Rep from the Showroom.')
    order_tags = fields.Many2many('order.tags',string='Order Tags',)
    
    
    @api.depends('order_line','production_ids','picking_ids','state')
    def _compute_open_shipments(self):   
        for sale in self:
            sale.open_production = False
            sale.open_shipment = False
            sale.received = False
            #1. mark the order as received if it has been confirmed.
            if sale.state not in ['draft','cancel','sent']:
                sale.received = True
            #2. open_shipment if there are any undelivered items on the SO.
            for line in sale.order_line:
                if line.qty_delivered < line.product_uom_qty:
                    if line.product_id.type != 'service' and 'Finish Sample' not in line.name:
                        if line.product_id.default_code not in ['F-FS04','F-FS01','MISC','F-CD05CH','F-CD09CH','F-CD13CH']:
                            if line.product_id.default_code not in ['F-CD14CH','F-CD18CH','F-CD19CH','F-CD40','F-CD41','DL-CD40']:
                                sale.open_shipment = True
                                break
                else:
                    sale.open_shipment = False
            #3. open production if there are any mrp.prods that are not done.
            for mrp in sale.production_ids:
                if mrp.state not in ['done','cancel']:
                    sale.open_production = True
                    break
                else:
                    sale.open_production = False
                    
                    
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    
    @api.depends('move_ids.state', 'move_ids.scrapped', 'move_ids.product_uom_qty', 'move_ids.product_uom')
    def _compute_qty_delivered(self):
        super(SaleOrderLine, self)._compute_qty_delivered()
        # TODO: do this in SQL
        for line in self:
            #if line.qty_delivered != line.product_uom_qty:
            qty = 0.0
            picking_ids = line.order_id.picking_ids
            domain = [('picking_id','in',picking_ids.ids),('product_id','=',line.product_id.id)]
            domain.append(('picking_id.state','!=','cancel'))
            domain.append(('state','=','done'))
            domain.append(('picking_id.picking_type_code','=','incoming'))
            in_moves = self.env['stock.move'].search(domain)
            #remove the 'IN' part of the domain and add the 'OUT' for 'out moves'
            domain.remove(('picking_id.picking_type_code','=','incoming'))
            domain.append(('picking_id.picking_type_code','=','outgoing'))
            out_moves = self.env['stock.move'].search(domain)
            #for pick in line.order_id.picking_ids:
            #    if pick.picking_type_code == 'OUT':
            for move in out_moves:
                qty += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom, rounding_method='HALF-UP')                   
            for move in in_moves:
                qty -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom, rounding_method='HALF-UP')
            #line.qty_delivered = qty <= line.product_uom_qty and qty or line.product_uom_qty
            line.qty_delivered = qty
                    
                        
                
            
        
         