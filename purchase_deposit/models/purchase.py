# Copyright 2019 Elico Corp, Dominique K. <dominique.k@elico-corp.com.sg>
# Copyright 2019 Ecosoft Co., Ltd., Kitti U. <kittiu@ecosoft.co.th>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def copy_data(self, default=None):
        if default is None:
            default = {}
        default["order_line"] = [
            (0, 0, line.copy_data()[0])
            for line in self.order_line.filtered(lambda l: not l.is_deposit)
        ]
        return super(PurchaseOrder, self).copy_data(default)
        
    sale_order_id = fields.Many2many('sale.order', string='Sale Order')

    @api.model
    def create(self, values):       
        if 'origin' in values and isinstance(values['origin'],str):
            # Checking first if this comes from a 'sale.order'
            sale_id = self.env['sale.order'].search([
                ('name', '=', values['origin'])
            ], limit=1)
            if sale_id:
                values['sale_order_id'] =  [(4,sale_id.id)]
                if sale_id.client_order_ref:
                    values['origin'] = sale_id.client_order_ref
            else:
                # Checking if this production comes from a route.
                # If from route, find procurement and get the sale_id from there
                source_docs = values['origin'].split(',')
                procure_id = self.env['procurement.group'].search([
                    ('name', 'in', source_docs)
                ])
                # If so, use the 'sale_id' from the parent production
                sale_id = procure_id and procure_id.sale_id
                sale_id = sale_id and sale_id.id or None
                if sale_id:
                    values['sale_order_id'] = [(4,sale_id.id)]
                    if sale_id.client_order_ref:
                        values['origin'] = sale_id.client_order_ref

        return super(PurchaseOrder, self).create(values)

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    is_deposit = fields.Boolean(
        string="Is a deposit payment",
        help="Deposit payments are made when creating invoices from a purhcase"
        " order. They are not copied when duplicating a purchase order.",
    )

    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        if self.is_deposit:
            res["quantity"] = -1 * self.qty_invoiced
        return res
