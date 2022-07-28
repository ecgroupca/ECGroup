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
        """Must find the pickings that are going to pre-production
           and then create a new picking from stock to pre-production
           for each of the workorders that exist for the MO, 
           grouping by their consumed in operation."""
        wo_obj = self.env['mrp.workorder']
        bom_line_obj = self.env['mrp.bom.line']
        pick_obj = self.env['stock.picking']        
        for order in self:
            picking_ids = pick_obj.search([
                ('group_id', '=', order.procurement_group_id.id),
                ('group_id', '!=', False),
            ])
            bom_id = order.bom_id
            for pick in picking_ids:
                new_picking_id = pick_obj
                if pick.picking_type_id.name=='Pick Components':
                    #loop through moves and assign workorders according to consumed in
                    for move in pick.move_lines:
                        domain = [('bom_id','=',bom_id.id),('product_id','=',move.product_id.id)]
                        bom_line = bom_line_obj.search(domain) and bom_line_obj.search(domain)[0] or False
                        domain = [('production_id','=',order.id),('operation_id','=',bom_line.operation_id.id)]
                        workorder_id = wo_obj.search(domain) and wo_obj.search(domain)[0] or False
                        pick_wo_id = pick.workorder_id
                        if not pick_wo_id:
                            pick.workorder_id = workorder_id
                            move.bom_line_id = bom_line and bom_line.id or False
                            move.workorder_id = workorder_id and workorder_id.id or False                           
                        elif pick_wo_id == workorder_id:
                            move.bom_line_id = bom_line and bom_line.id or False
                            move.workorder_id = workorder_id and workorder_id.id or False
                            move.picking_id = pick.id                           
                        else: 
                            #find the picking that was created for the workorder and assign the move                        
                            wo_pick = pick_obj.search([('workorder_id','=',workorder_id.id)])
                            if wo_pick:
                                move.picking_id = wo_pick.id
                                move.bom_line_id = bom_line and bom_line.id or False
                                move.workorder_id = workorder_id and workorder_id.id or False 
                            else:
                                #create a new picking and reassign this move to the new pick.
                                new_picking_id = pick.copy()
                                new_picking_id.move_lines.unlink()
                                move.picking_id = new_picking_id.id
                                move.bom_line_id = bom_line and bom_line.id or False
                                move.workorder_id = workorder_id and workorder_id.id or False 
                                new_picking_id.workorder_id = workorder_id
                                self._compute_picking_ids()
                        
                order.picking_ids |= pick
                if new_picking_id:
                    order.picking_ids |= new_picking_id
            order.delivery_count = len(order.picking_ids)                     
        
    def _action_cancel(self):
        documents_by_production = {}
        for production in self:
            documents = defaultdict(list)
            for move_raw_id in self.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                iterate_key = self._get_document_iterate_key(move_raw_id)
                if iterate_key:
                    document = self.env['stock.picking']._log_activity_get_documents({move_raw_id: (move_raw_id.product_uom_qty, 0)}, iterate_key, 'UP')
                    for key, value in document.items():
                        documents[key] += [value]
            if documents:
                documents_by_production[production] = documents
            # log an activity on Parent MO if child MO is cancelled.
            finish_moves = production.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            if finish_moves:
                production._log_downside_manufactured_quantity({finish_move: (production.product_uom_qty, 0.0) for finish_move in finish_moves}, cancel=True)

        self.workorder_ids.filtered(lambda x: x.state not in ['done', 'cancel']).action_cancel()
        finish_moves = self.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        raw_moves = self.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))

        (finish_moves | raw_moves)._action_cancel()
        #ADAM O - Added and 'Return' not in x.origin to domain so that we no longer cancel any pickings that are returns
        picking_ids = self.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel') and (x.origin and 'Return' not in x.origin))
        picking_ids.action_cancel()

        for production, documents in documents_by_production.items():
            filtered_documents = {}
            for (parent, responsible), rendering_context in documents.items():
                if not parent or parent._name == 'stock.picking' and parent.state == 'cancel' or parent == production:
                    continue
                filtered_documents[(parent, responsible)] = rendering_context
            production._log_manufacture_exception(filtered_documents, cancel=True)

        # In case of a flexible BOM, we don't know from the state of the moves if the MO should
        # remain in progress or done. Indeed, if all moves are done/cancel but the quantity produced
        # is lower than expected, it might mean:
        # - we have used all components but we still want to produce the quantity expected
        # - we have used all components and we won't be able to produce the last units
        #
        # However, if the user clicks on 'Cancel', it is expected that the MO is either done or
        # canceled. If the MO is still in progress at this point, it means that the move raws
        # are either all done or a mix of done / canceled => the MO should be done.
        self.filtered(lambda p: p.state not in ['done', 'cancel'] and p.bom_id.consumption == 'flexible').write({'state': 'done'})
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

        return True
        
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