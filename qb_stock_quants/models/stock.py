# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api


class ReservedOrder(models.Model):
    _name = 'reserved.order'
    _description = 'Reserved Orders'
    
    name = fields.Char('Name')
    quant_id = fields.Many2one('stock.quant',string = 'Quant')
    move_line_id = fields.Many2one('stock.move.line',string = 'Product Move')
    product_id = fields.Many2one('product.product',string = 'Product',related='move_line_id.product_id')
    product_uom_qty = fields.Float('Qty Reserved',related='move_line_id.product_uom_qty')
    picking_id = fields.Many2one('stock.picking', string = 'Transfer',related='move_line_id.picking_id')
    production_id = fields.Many2one('mrp.production', string = 'Production Order',related='move_line_id.production_id')

class StockQuant(models.Model):
    """Stock Quant"""

    _inherit = 'stock.quant'
    
    """reserved_order_names = fields.Char(
        'Reserved Orders',
        compute = '_compute_reserved_orders'
    )"""

    reserved_order_ids = fields.Many2many(
        'reserved.order',
        string='Reserved Orders',
        compute = '_compute_reserved_orders'
    )
    
    def _compute_reserved_orders(self):
        for quant in self:
            quant.reserved_order_ids = [(4, False)] 
            res_line_ids = quant.product_id\
               and quant.product_id.reserved_line_ids
            orders = {}
            for line in res_line_ids: 
                if quant.lot_id == line.lot_id and quant.location_id == line.location_id:            
                    trans = line.move_id.raw_material_production_id or line.picking_id or None
                    pick_type = trans and trans.picking_type_id or None
                    if pick_type and pick_type.code in ['mrp_operation','outgoing','internal']:
                        if line.state not in ['cancel']:
                            if trans and trans.name in orders:
                                orders[trans.id] = trans.name 
                            else:
                                vals = {
                                    'quant_id': quant.id,
                                    'move_line_id': line.id, 
                                    'name': trans and trans.name + ': ' + str(line.product_uom_qty),                            
                                }
                                reserved_order = self.env['reserved.order'].sudo().create(vals)
                                quant.reserved_order_ids = [(4, reserved_order.id)]                       
                
class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    reserved_line_ids = fields.One2many(
        'stock.move.line',
        'product_id',
        'Reserved move lines',
        compute = '_compute_moves'
    )
    
    def _compute_moves(self):
        for product in self:
            domain = [
                ('product_uom_qty','>',0),
                ('product_id','=',product.id),
            ]
            move_lines = self.env['stock.move.line'].search(domain)
            product.reserved_line_ids = [(6, 0, move_lines.ids)]