# -*- coding: utf-8 -*-
#############################################################################
#
#    Quickbeam ERP.
#
#    Copyright (C) 2020-TODAY, Quickbeam, LLC.
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

 
class AccountPayment(models.Model):
    _inherit = "account.payment"
    
    def post(self):
        res = super(AccountPayment,self).post()
        #assign the pmt_id for each commission paid by this one.
        if res:
            for pmt in self:
                for invoice in pmt.invoice_ids:
                    commisssions = self.env['sale.commission'].search([('invoice_id','=',invoice.id)])
                    for comm in commissions:
                        comm.pmt_id = pmt
        
        return res
        
        
class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    has_comm_inv = fields.Boolean('Commission Invoice Exists')
    
    def action_confirm(self): 
        res = super(SaleOrder,self).action_confirm()
        #create new commissions object
        for line in self.order_line:
            if not line.product_id.no_commissions and line.product_id.type != 'service':
                client_po = self.client_order_ref and str(self.client_order_ref) or ''
                vals = {
                    'name': 'Order: ' + self.name  + ' commissions.',
                    'ref':client_po,
                    'order_line': line.id,
                    'state': 'draft',
                    }
                self.env['sale.commission'].create(vals)
        return res
        
    def pay_commission(self):    
        self._create_comm_invoices()

        inv_form = self.env.ref('account.view_move_form', False)

        return {

        'name': 'Sales Commission Invoice',

        'type': 'ir.actions.act_window',

        'res_model': 'account.move',

        'view_type': 'form',

        'view_mode': 'tree,form',

        'target': 'self',

        'views': [(inv_form.id, 'form')],

        'view_id': 'inv_form.id',

        'flags': {'action_buttons': True},

        }
        return {
            'name': _('My Form'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }
            
    def _prepare_comm_invoice(self):
        """
        Prepare the dict of values to create the new vendor bill for a commission on a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        # ensure a correct context for the _get_default_journal method and company-dependent fields
        self = self.with_context(default_company_id=self.company_id.id, force_company=self.company_id.id)
        journal = self.env['account.move'].with_context(default_type='in_invoice')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))
        team =  self.team_id
        team_id = team and team.id or False
        
        invoice_vals = {
            'ref': self.client_order_ref or '',
            'type': 'in_invoice',
            'narration': self.note,
            'currency_id': self.pricelist_id.currency_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'team_id': team_id,
            'partner_id': team and team.user_id and team.user_id.id or False,
            'invoice_partner_bank_id': self.company_id.partner_id.bank_ids[:1].id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.name,
            'invoice_payment_ref': self.reference,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals
        
    def _create_comm_invoices(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        comm = self.env['sale.commission']
        inv = self.env['account.move']
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        # 1) Create invoices.
        invoice_vals_list = []
        for order in self:

            invoice_vals = order._prepare_comm_invoice()
            comm_lines = comm.sudo().search([('order_id','=',order.id),('pmt_id','=',False),('invoice_id','=',False),])
            
            if not comm_lines:
                raise UserError(_('No commissionable lines found.'))

            invoice_vals['invoice_line_ids'] = [
                (0, 0, line._prepare_comm_invoice_line())
                for line in comm_lines
            ]

            invoice_vals_list.append(invoice_vals)
            # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
            # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
            moves = self.env['account.move'].sudo().with_context(default_type='in_invoice').create(invoice_vals_list)
            order.has_comm_inv = moves and move[0] and True or False
            if moves and moves[0]:
                for line in comm_lines:
                    line.invoice_id = moves and moves[0] or False               
        return moves
    

class SaleCommission(models.Model):
    _name = "sale.commission"
    _description = 'Sales Commission'
    
    order_line = fields.Many2one('sale.order.line', 
        string='Sale Line', copy=True,
        )
    order_id = fields.Many2one('sale.order', 'Sale Order',
        related = 'order_line.order_id'
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
    invoice_id = fields.Many2one('account.move.line',
        'Invoice',
        )
    invoice_state = fields.Selection('Invoice State',
        related = 'invoice_id.move_id.state',
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
        if line:
            prod_ob = self.env['product.product']
            product_id = prod_ob.search(
                [('name','=','Sales Commissions')]
            )
            product_id = product_id and product_id[0] or False
            account_id = product_id and product_id.property_account_expense_id or False
            res = {
                'display_type': False,
                'sequence': line.sequence,
                'name': 'Commissions for sale: ' + line.order_id.name + ' item:' + line.name,
                'quantity': 1,
                'price_unit': line.comm_rate*line.price_unit*line.product_uom_qty/100,
                'analytic_account_id': line.order_id.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                'sale_line_ids': [(4, line.id)],
                'product_id': product_id and product_id.id or False,
                'account_id': account_id and account_id.id or False,
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