from odoo import fields, models, api, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    mrp_ids = fields.Many2many(
        'mrp.production',
        string = 'MOs',
        readonly = False,
        compute='_compute_mrp_ids'
    )

    mrp_orders_counted = fields.Integer(
        "MRP Order Count",
        compute='_compute_mrp_orders_counted',)
        
    sale_order_id = fields.Many2many(
        'sale.order',
        string = 'Sales',
        readonly = False,
    )

    sale_orders_counted = fields.Integer(
        "Sale Order Count",
        compute='_compute_sale_orders_counted',)
        
    @api.depends("mrp_ids")
    def _compute_mrp_orders_counted(self):
        for purchase in self:
            purchase.mrp_orders_counted = len(purchase.mrp_ids)
        
    @api.depends("mrp_ids")
    def _compute_mrp_ids(self):
        for purchase in self:
            mrp_ids = []
            for line in purchase.order_line:
                mrp_ids += line.mrp_order_ids
            purchase.mrp_ids = [(6,0,mrp_ids)]
            
    def action_view_mrp(self):
        self.ensure_one()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = (
            self.env.ref("mrp.mrp_production_action")
            .with_context(active_id=self.id)
            .read()[0]
        )
        mrp_orders = self.mrp_order_ids
        if len(mrp_orders) > 1:
            action["domain"] = [("id", "in", mrp_orders.ids)]
        elif mrp_orders:
            action.update(
                res_id=mrp_orders.id, 
                view_mode="form", 
                view_id=False, 
                views=False,
            )
        return action  
        
    @api.depends("sale_order_id")
    def _compute_sale_orders_counted(self):
        for purchase in self:
            purchase.sale_orders_counted = len(purchase.sale_order_id)
            
    def action_view_sale_orders(self):
        self.ensure_one()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = (
            self.env.ref("sale.action_quotations")
            .with_context(active_id=self.id)
            .read()[0]
        )
        sales = self.sale_order_id
        if len(sales) > 1:
            action["domain"] = [("id", "in", sales.ids)]
        elif sales:
            action.update(
                res_id=sales.id, 
                view_mode="form", 
                view_id=False,
                views=False,
            )
        return action

    def copy_data(self, default=None):
        if default is None:
            default = {}
        default["order_line"] = [
            (0, 0, line.copy_data()[0])
            for line in self.order_line.filtered(lambda l: not l.is_deposit)
        ]
        return super(PurchaseOrder, self).copy_data(default)

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
    sale_order_id = fields.Many2one(
        related='sale_line_id.order_id', 
        string="Sale Order", 
        store=True, readonly=True)
        
    sale_line_id = fields.Many2one(
        'sale.order.line', 
        string="Origin Sale Item", 
        index=True, copy=False)
    
    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        if self.is_deposit:
            res["quantity"] = -1 * self.qty_invoiced
        return res
