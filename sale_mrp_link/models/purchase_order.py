# Copyright 2018 Alex Comba - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sale_order_id = fields.Many2many(
        'sale.order',
        string = 'Sale Orders',
        compute = "_compute_sale_orders",
        readonly = False,
        store = True,
    )

    sale_order_count = fields.Integer(
        "Number of Source Sale",
        compute='_compute_sale_order_count',
        groups='sales_team.group_sale_salesman')
        
    @api.depends('order_line.sale_order_id','sale_order_id')
    def _compute_sale_order_count(self):
        for purchase in self:
            count = len(purchase.sale_order_id)
            purchase.sale_order_count = count

    @api.depends('order_line.sale_order_id','sale_order_id')    
    def _compute_sale_orders(self):
        for purchase in self:
            purchase.sale_order_id = [(4, False)]
            #search for purchases that reference the sale
            domain = [('id','in',purchase.order_line.sale_order_id.ids)]
            domain += [('id','in',purchase.sale_order_id.ids)]
            domain += [('company_id','=',purchase.company_id.id)]
            sale_ids = self.env['sale.order'].search(domain)
            purchase.sale_order_id = [(6, 0, sale_ids.ids)]
            
    def action_view_sale_orders(self):
        self.ensure_one()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        sale_order_ids = self.sale_order_id.ids
        action = {
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
        }
        if len(sale_order_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': sale_order_ids[0],
            })
        else:
            action.update({
                'name': _('Sources Sale Orders %s', self.name),
                'domain': [('id', 'in', sale_order_ids)],
                'view_mode': 'tree,form',
            })
        return action
