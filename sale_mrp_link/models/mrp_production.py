# Copyright 2018 Alex Comba - Agile Business Group
# Copyright 2016-2018 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order', readonly=False, string='Sale Order')
        
    sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line', readonly=False, string='Source Sale Order Line.')    

    desc_from_line = fields.Char(
        'Sale Line Description',
        compute = '_get_line_desc'
    )
    
    sale_count = fields.Integer(
        compute='_compute_sale_count', store=True)
        
    @api.depends("sale_order_id")
    def _compute_sale_count(self):
        for mrp in self:
            mrp.sale_count = len(mrp.sale_order_id)
          
    def action_view_sales(self):
        """Invoked when 'Sale Orders' smart button in rma form view is clicked."""
        action = (
            self.env.ref("sale.action_quotations")
            .with_context(active_id=self.id)
            .read()[0]
        )
        sales = self.sale_ids
        if len(sales) > 1:
            action["domain"] = [("id", "in", sales.ids)]
        elif sales:
            action.update(
                res_id=sales.id, view_mode="form", view_id=False, views=False,
            )
        return action
    
    @api.depends('sale_order_id')     
    def _get_line_desc(self):
        for mrp in self:
            sale_id = mrp.sale_order_id
            #search for the sale line with the product from MRP
            sale_line = self.env['sale.order.line'].search([
                ('product_id', '=', mrp.product_id),
                ('product_uom_qty','=',mrp.product_uom_qty),
                ]
            )
            if sale_line:
                mrp.sale_order_line_id = sale_line
                mrp.desc_from_line = sale_line.name

    
    @api.model
    def create(self, values):
        if 'origin' in values:
            # Checking first if this comes from a 'sale.order'
            sale_id = self.env['sale.order'].search([
                ('name', '=', values['origin'])
            ], limit=1)
            if sale_id:
                values['sale_order_id'] = sale_id.id
                if sale_id.client_order_ref:
                    values['origin'] = sale_id.client_order_ref
            else:
                # Checking if this production comes from a route
                production_id = self.env['mrp.production'].search([
                    ('name', '=', values['origin'])
                ])
                # If so, use the 'sale_order_id' from the parent production
                if production_id and production_id.sale_order_id:
                    values['sale_order_id'] = production_id.sale_order_id.id

        return super(MrpProduction, self).create(values)
