# -*- coding: utf-8 -*-
#############################################################################
#
#    Quickbeam ERP.
#
#    Copyright (C) 2021-TODAY, Quickbeam, LLC.
#    Author: Adam O'Connor <aoconnor@quickbeamllc.com>
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleCommission(models.Model):
    _name = "sale.commission"
    _description = 'Sales Commission'
    
    order_line = fields.Many2one('sale.order.line', 
        string='Sale Line', copy=True,
        )
    order_id = fields.Many2one('sale.order', 'Sale Order',
        related = 'order_line.order_id'
        )
    team_id = fields.Many2one('crm.team', 'Showroom',
        related = 'order_line.order_id.team_id'
        )
    commissions_payee_id = fields.Many2one('res.users', 'Salesperson',
        related = 'order_line.order_id.team_id.user_id'
        )
    name = fields.Char('Description', index=True)
    ref = fields.Char('Reference')
    partner_id = fields.Many2one('res.partner',
        "Customer",
        related = 'order_line.order_id.partner_id')
    comm_rate = fields.Float("Comm Rate",
        related = 'order_line.comm_rate',
        )
    product_uom_qty = fields.Float("Quantity",
        related = 'order_line.product_uom_qty',
        )
    price_unit = fields.Float("Price",
        related = 'order_line.price_unit',
        )
    comm_total = fields.Float(
        "Comm Total",
        compute="_compute_comm_total",
        store = True,
        )
    state = fields.Selection([
        ('draft', 'New'),
        ('cancel', 'Cancelled'),
        ('confirmed', 'Awaiting Payment'),
        ('paid', 'Paid')], string='Status',
        copy=False, default='draft', index=True, readonly=True,
        )
    company_id = fields.Many2one('res.company',
        string='Company',
        related = "order_line.order_id.company_id"
        )
    invoice_id = fields.Many2one('account.move',
        'Invoice',
        )
    invoice_state = fields.Selection('Invoice State',
        related = 'invoice_id.state',
        )
    pmt_id = fields.Many2one('account.payment',
        'Payment',
        )
    pmt_state = fields.Selection('Payment State',
        related = 'pmt_id.state',
        )
    
    """ Invoice Date
	    Invoice Total*
	    Payment Status
	    Payment Amount"""
        
    #need method that creates the commission record when the sale is confirmed
    #and subsequent lines added to a confirmed sale on save must create a commission record if comm_rate > 0
    """def pay_commission(self):
        for sale in self:
            comm = self.env['sale.commission']
            comm_lines = comm.search([('order_id','=',sale.id)])
            #create a vendor invoice and input the lines from the sale order
            inv = self.env['account.move']
            vals = {}
            invoice = inv.create(vals)"""
            
    
    def _prepare_comm_invoice_line(self):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        line = self.order_line
        res = {}
        company_id = self.company_id and self.company_id.id or None
        if line and company_id:
            prod_ob = self.env['product.product']
            product_id = prod_ob.search(
                [('name','=','Sales Commissions'),('company_id','=',company_id)]
            )
            product_id = product_id and product_id[0] or False
            account_id = product_id and product_id.property_account_expense_id or False
            res = {
                'display_type': False,
                'sequence': line.sequence,
                'name': 'Commissions for sale: ' + line.order_id.name + ' | item:' + line.name,
                'quantity': 1,
                'price_unit': line.comm_rate*line.price_unit*line.product_uom_qty/100,
                'analytic_account_id': line.order_id.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                'sale_line_ids': [(4, line.id)],
                'product_id': product_id and product_id.id or False,
                'account_id': account_id and account_id.id or False,
                'sale_line_ids': [(6, 0, [line.id])],
            }
        return res
        
    @api.depends('order_line')
    def _compute_comm_total(self):
        for comm in self:
            line = comm.order_line
            sale = line.order_id
            if not line.product_id.no_commissions:   
                qty_to_deliver = 0
                total_comm = 0
                amt_due = 0
                amt_res = 0
                amt_inv = 0                                      
                for invoice in sale.invoice_ids:
                    if invoice.state=='posted':
                        amt_res += invoice.amount_residual
                        amt_inv += invoice.amount_total
                amt_due = (sale.amount_total - amt_inv) + amt_res
                for order_line in sale.order_line:
                    qty_to_deliver += order_line.qty_to_deliver                   
                if amt_due <= 0.00 and qty_to_deliver == 0:
                    #calc the commission for this object
                    total_comm = line.comm_rate and line.comm_rate*line.price_unit*line.product_uom_qty/100
                    comm.comm_total = total_comm                
                sale.inv_bal_due = amt_due