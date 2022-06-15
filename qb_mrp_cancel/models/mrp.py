from odoo import api, fields, models, _
from collections import defaultdict

        
class MRPProduction(models.Model):
    _inherit = "mrp.production"
    
    picking_ids = fields.Many2many(
        'stock.picking',
        store = True, 
        compute='_compute_picking_ids',         
        string='Pickings',
        )
        
    @api.depends('procurement_group_id')
    def _compute_picking_ids(self):
        for order in self:
            picking_ids = self.env['stock.picking'].search([
                ('group_id', '=', order.procurement_group_id.id),
                ('group_id', '!=', False),
            ])
            for pick in picking_ids:
                order.picking_ids |= pick
            order.delivery_count = len(order.picking_ids)
        
    def _action_cancel(self):
        done_picking_ids = self.picking_ids.filtered(lambda x: x.state in ('done') and 'Return' not in x.origin)
        for pick in done_picking_ids:
            return_picking = self.picking_ids.filtered(lambda x: x.origin == 'Return of %s'% pick.name)
            if not return_picking:
                #launch wizard action to create returns for each picking using the wizard
                #create a new picking that reverses this done picking and confirm and process it to done
                new_picking = pick.copy(self._prepare_picking_default_values(pick))
                for return_move in pick.move_lines:
                    if return_move.product_uom_qty:
                        vals = self._prepare_move_default_values(return_move, new_picking)
                        r = return_move.copy(vals)
                        
                new_picking.action_confirm()
                new_picking.action_assign()   
                """for move in new_picking.move_lines:
                    move.state = 'done'   
                    move.quantity_done = move.product_uom_qty                    
                new_picking.state = 'done'"""
                self.picking_ids |= new_picking
        res = super(MRPProduction, self)._action_cancel()
        return res
        
    def _prepare_move_default_values(self, return_move, new_picking):
        vals = {
            'product_id': return_move.product_id.id,
            'product_uom_qty': return_move.product_uom_qty,
            'product_uom': return_move.product_id.uom_id.id,
            'picking_id': new_picking.id,
            'state': 'draft',
            'date': fields.Datetime.now(),
            'location_id': return_move.location_dest_id.id,
            'location_dest_id': return_move.location_id.id,
            'picking_type_id': new_picking.picking_type_id.id,
            'warehouse_id': new_picking.picking_type_id.warehouse_id.id,
            'origin_returned_move_id': return_move.id,
            'procure_method': 'make_to_stock',
        }
        return vals
        
    def _prepare_picking_default_values(self,picking_id):
        return {
            'move_lines': [],
            'picking_type_id': picking_id.picking_type_id.return_picking_type_id.id or picking_id.picking_type_id.id,
            'state': 'draft',
            'origin': _("Return of %s") % picking_id.name,
            'location_id': picking_id.location_dest_id.id,
            'location_dest_id': picking_id.location_id.id
        }