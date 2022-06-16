from odoo import fields, models, api
from odoo.addons import decimal_precision as dp
from odoo.exceptions import Warning


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    state = fields.Selection(selection_add=[('reserved', 'Reserved')])
    production_bom_ids = fields.One2many('production.bom', 'production_id', 'Production BOM')
    new_order = fields.Boolean('New Order',
                               help='This is the field to identify only if the order was created before installation of module or after'
                                    'If the production order was created pre installation this module should not change the wrokflow for that order')

    full_reserved = fields.Boolean('Full Reserved ?', compute='check_full_reserve', store=False)

    @api.depends('move_raw_ids.reserved_availability', 'production_bom_ids.reserved_qty')
    def check_full_reserve(self):
        for record in self:
            reserved = True
            for line in self.production_bom_ids:
                if not line.substitute_product_id and line.product_id.type == 'product':
                    if line.required_qty != sum((line + self.production_bom_ids.filtered(
                            lambda l: l.substitute_product_id == line.product_id)).mapped('reserved_qty')):
                        reserved = False
            if reserved:
                record.full_reserved = True
            else:
                record.full_reserved =False

    @api.depends('move_raw_ids')
    def _has_moves(self):
        for mo in self:
            mo.has_moves = any(mo.move_raw_ids) or any(mo.production_bom_ids)

    @api.model
    def create(self, vals):
        vals.update({'new_order': True})
        production = super(MrpProduction, self).create(vals)
        production.generate_production_bom()
        return production

    def write(self, vals):
        for record in self:
            super(MrpProduction, self).write(vals)
            if 'product_id' in vals.keys() and record.new_order:
                record.generate_production_bom()
        return True

    def do_unreserve(self):
        for production in self:
            production.move_finished_ids._action_cancel()
            production.move_finished_ids.unlink()
            production.production_bom_ids.write({'reserved_qty': 0})
            result = super(MrpProduction, production).do_unreserve()
            if production.new_order:
                production.move_raw_ids._action_cancel()
                production.move_raw_ids.unlink()
                production.write({'state': 'confirmed'})
        return result


    def update_production_bom(self, bom_line, sequence=1):
        products = bom_line.product_id + bom_line.substitute_product_ids
        if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom':
            return
        if bom_line.product_id.type not in ['product', 'consu']:
            return
        for product in products:
            self.env['production.bom'].create({
                'sequence': sequence,
                'name': self.name,
                'bom_line_id': bom_line.id,
                'product_id': product.id,
                'product_uom_qty': self.product_qty * (bom_line.product_qty / self.bom_id.product_qty),
                'required_qty': self.product_qty * (bom_line.product_qty / self.bom_id.product_qty),
                'product_uom': bom_line.product_uom_id.id,
                'production_id': self.id,
                'substitute_product_id': bom_line.product_id.id if bom_line.substitute_product_ids and product != bom_line.product_id else False,
            })

        return True

    def set_consumable_qty(self):
        for line in self.production_bom_ids:
            if not line.substitute_product_id and line.product_id not in self.production_bom_ids.mapped(
                    'substitute_product_id'):
                line.write({'consumable_qty': line.required_qty})
        return True

    def generate_production_bom(self):
        self.production_bom_ids.unlink()
        sequence = 0
        for line in self.bom_id.bom_line_ids:
            sequence += 1
            self.update_production_bom(line, sequence)
        self.set_consumable_qty()
        return True


    def _get_moves_raw_values(self):
        '''Do not generate raw moves on saving of record for new record'''
        if not self.new_order:
            super(MrpProduction, self)._get_moves_raw_values()
        return []


    def generate_raw_moves(self, line, sequence=1):
        bom_line = line.bom_line_id
        # we check stock only for stockable products
        quantity = min(line.consumable_qty, line.available_qty)
        line.reserved_qty = quantity
        source_location = self.location_src_id
        original_quantity = (self.product_qty - self.qty_produced) or 1.0
        if quantity > 0:
            data = {
                'sequence': sequence,
                'name': self.name,
                'date': self.date_planned_start,
                'date_deadline': self.date_planned_start,
                'bom_line_id': bom_line.id,
                'product_id': line.product_id.id,
                'product_uom_qty': quantity,
                'product_uom': bom_line.product_uom_id.id,
                'location_id': source_location.id,
                'location_dest_id': self.product_id.property_stock_production.id,
                'raw_material_production_id': self.id,
                'company_id': self.company_id.id,
                'price_unit': bom_line.product_id.standard_price,
                'procure_method': 'make_to_stock',
                'origin': self.name,
                'warehouse_id': source_location.warehouse_id.id,
                'group_id': self.procurement_group_id.id,
                'unit_factor': quantity / original_quantity,
            }
            move = self.env['stock.move'].create(data)
            line.move_id = move.id
            return move

    def validate_order(self):
        for production in self:
            if 'e' in production.production_bom_ids.mapped('error_status'):
                raise Warning(u'Por favor corrija as linhas com erro!!')
            production.check_full_reserve()
            for line in self.production_bom_ids:
                if not line.substitute_product_id:
                    reserved_qty = sum((line + self.production_bom_ids.filtered(
                            lambda l: l.substitute_product_id == line.product_id)).mapped('reserved_qty'))
                    if line.required_qty != reserved_qty:
                        raise Warning('Only %s reserved but %s requried for product %s' % (
                            reserved_qty, line.required_qty, line.product_id.name))
        return True

    def open_produce_product(self):
        for production in self:
            production.validate_order()
        return super(MrpProduction, self).open_produce_product()

    def reserve_items(self):
        self.do_unreserve()
        for production in self:
            ## Unlink finished moves if exist we need to change it if someone has updated quantity
            ## Generate finished move again
            production._onchange_move_finished()
            sequence = 0
            for line in production.production_bom_ids:
                sequence +=1
                production.generate_raw_moves(line, sequence)
            production.move_raw_ids._action_confirm()
            production.action_assign()
            # production.write({'state' :'planned'})
        return True


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    substitute_product_ids = fields.Many2many('product.product', 'bom_optional_product_rel', 'bom_id', 'product_id',
                                              string='Substitute Products')


class ProductionBom(models.Model):
    _name = 'production.bom'

    name = fields.Char('Name')
    sequence = fields.Char('Sequence')
    product_id = fields.Many2one('product.product', 'Product')
    product_qty = fields.Float(related='product_id.qty_available_not_res', string='Available Qty ')
    available_qty = fields.Float(compute='get_available_qty', string='Available Qty')
    substitute_product_id = fields.Many2one('product.product', 'Substitute Product')
    product_uom = fields.Many2one('uom.uom', 'UoM')
    product_uom_qty = fields.Float('Reserved', default=0.0, digits=(16, 2),
                                   required=True)
    required_qty = fields.Float('Required Qty', readonly=True)
    consumable_qty = fields.Float('Comsumable Qty')
    move_id = fields.Many2one('stock.move', 'Stock Move')
    reserved_qty = fields.Float(related='move_id.reserved_availability', store=False, string='Reserved Qty')
    status = fields.Selection([('d', 'Draft'), ('a', 'Available'), ('w', 'Waiting for Availability'), ('do', 'Done')],
                              default='d', compute='_get_availability', required=True, string='Status')
    production_id = fields.Many2one('mrp.production', 'Production Order')
    bom_line_id = fields.Many2one('mrp.bom.line', 'BOM Line')
    error_status = fields.Selection([('e', 'Error'), ('o', 'Ok'), ('d', 'Done')], compute='check_error_staus',
                                    store=False,
                                    string='Error Status')
    def get_available_qty(self):
        for record in self:
            if record.product_id and record.product_id.type == 'product':
                record.available_qty = record.product_qty
            else:
                record.available_qty = record.required_qty


    def check_error_staus(self):
        for record in self:
            qty = record.required_qty
            lines = record.search([('production_id', '=', record.production_id.id), ('bom_line_id', '=', record.bom_line_id.id)])
            if record.production_id.state == 'done':
                record.error_status = 'd'
            elif sum([line.consumable_qty for line in lines]) == qty:
                record.error_status = 'o'
            else:
                record.error_status = 'e'

    def _get_availability(self):
        for record in self:
            if record.product_id.type != 'product':
                record.status = 'a'
            elif record.available_qty + record.reserved_qty >= record.required_qty:
                record.status = 'a'
            else:
                record.status = 'w'