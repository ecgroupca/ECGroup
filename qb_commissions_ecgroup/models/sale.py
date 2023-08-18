# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import UserError
from odoo import models, fields, api, _
import datetime

         
class CRMTeam(models.Model):
    _inherit = 'crm.team'
    
    comm_inv_partner = fields.Many2one(
        'res.partner',
        string = "Commission Invoice Address",        
        copy = False,
        stored = True,
    )
    
    default_comm_rate = fields.Float(
        'Default Commission Rate (%)', 
        readonly = False,
        stored = True,
    )


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def create(self, vals):
        if 'order_id' in vals:
            def_comm_rate = self.env['sale.order'].browse(vals['order_id'])
            def_comm_rate = def_comm_rate and def_comm_rate.team_id
            def_comm_rate = def_comm_rate and def_comm_rate.default_comm_rate
            vals['comm_rate'] = def_comm_rate
        return super(SaleOrderLine, self).create(vals)
            
        
        
class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    comm_rate = fields.Float(
        string="Commission Rate",
        store = True,
        )
        
    fully_paid_date = fields.Date(
        'Fully Paid Date',
        )
        
    fully_shipped_date = fields.Datetime(
        'Fully Shipped Date',
        )
   
    comm_total = fields.Float(
        'Total Commisions', 
        compute="_compute_comm_total",
        store = True,
        )
    
    comm_inv_paid = fields.Boolean(
        'Commission Invoice Paid?',
        copy=False,
        readonly=False,
        store=True,
    )
    
    comm_inv_id = fields.Many2one(
        'account.move',
        string='Commission Invoice',
        copy=False,
        readonly=True,
    )     
    
    """@api.depends('team_id')     
    def _compute_comm_rate(self):
        for sale in self:
            sale.comm_rate = sale.team_id and sale.team_id.default_comm_rate or 0.00  
            header_rate = sale.comm_rate
            for line in sale.order_line:
                if line.product_id and not line.product_id.no_commissions: 
                    if line.product_id.type not in ['service','consu']:
                        line.comm_rate = header_rate"""
            
    @api.onchange('comm_rate')
    def _onchange_comm_rate(self):   
        for sale in self:
            header_rate = sale.comm_rate
            if header_rate:
                for line in sale.order_line:
                    if line.product_id and not line.product_id.no_commissions: 
                        if line.product_id.type not in ['service','consu']:
                            line.comm_rate = header_rate
                            
    @api.onchange('team_id')
    def _onchange_sales_team(self):
        for sale in self:
            def_comm_rate = sale.team_id.default_comm_rate
            sale.comm_rate = def_comm_rate
            for line in sale.order_line:
                if line.product_id and not line.product_id.no_commissions: 
                    if line.product_id.type not in ['service','consu']:
                        line.comm_rate = def_comm_rate
    
    #1. compute the total commission for an order
    #2. base the report on sale order (lines) instead of these comm objects
    #3. base the comm_inv_paid on the comm_inv_id
    #4. report on amount of commissions paid for a given order that has 
    #   non-zero comm rate on at least one line
    @api.depends('order_line')
    def _compute_comm_total(self):
        for sale in self:
            total_comm = 0
            for line in sale.order_line:
                line_comm = 0
                if line.comm_rate and line.price_unit and line.product_uom_qty:
                    if line.product_id and not line.product_id.no_commissions and line.product_id.type not in ['service','consu']:
                        line_comm = line.comm_rate*line.price_unit*line.product_uom_qty/100
                        total_comm += line_comm
                    else:
                        line.comm_rate = 0
            sale.comm_total = total_comm  
            
    @api.depends('comm_inv_id')
    def _commission_inv_paid(self):
        for order in self:
            order.comm_inv_paid = False
            #if commission invoice is paid, then we mark it so.
            if order.comm_inv_id and order.comm_inv_id.amount_residual==0.00:
                order.comm_inv_paid = True
    
    def action_confirm(self): 
        res = super(SaleOrder,self).action_confirm()
        #create new commissions object
        #set the commissions rate for each line to the default from the showroom
        for sale in self:
            def_comm_rate = sale.team_id.default_comm_rate
            sale.comm_rate = def_comm_rate
            #for line in sale.order_line:
            #    if line.product_id and not line.product_id.no_commissions: 
            #        if line.product_id.type not in ['service','consu']:
            #            line.comm_rate = def_comm_rate
            sale._compute_comm_total()
            for line in sale.order_line:
                if line.product_id.type != 'service':              
                    if not line.tax_id:
                        UserError(_('Must have a tax on every non-service line.'))
                    if line.product_id.type != 'consu':
                        if line.comm_rate and not line.product_id.no_commissions:
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
    
        move = self._create_comm_invoices()
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
            'context': self._context,
            'res_id': move and move.id or False,
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
            'ref': str(self.name) + ' - ' + str(self.client_order_ref),
            'type': 'in_invoice',
            'narration': self.note,
            'currency_id': self.pricelist_id.currency_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'team_id': team_id,
            #'partner_id': team and team.user_id and team.user_id.partner_id and team.user_id.partner_id.id or False,
            'partner_id': team and team.comm_inv_partner and team.comm_inv_partner or False,
            'invoice_partner_bank_id': self.company_id.partner_id.bank_ids[:1].id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.name,
            'invoice_payment_ref': self.reference,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
            'invoice_line_ids': [],
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
        
        done = False
        for order in self:
            if order.state not in ['draft','cancel'] and order.inv_bal_due <= 0.00:
                done = True
                for line in order.order_line:
                    if line.product_id.type == 'product' and line.product_uom_qty > line.qty_delivered:
                        done = False
                        break
            if done:
                invoice_vals_list = []
                invoice_vals = order._prepare_comm_invoice()
                comm_lines = comm.sudo().search([('order_id','=',order.id),('pmt_id','=',False),('invoice_id','=',False),])           
                if not comm_lines:
                    #create new commissions objects because they haven't been created before.
                    for line in order.order_line:
                        if line.comm_rate and not line.product_id.no_commissions and line.product_id.type not in ['service','consu']:
                            client_po = self.client_order_ref and str(self.client_order_ref) or ''
                            vals = {
                                'name': 'Order: ' + order.name  + ' commissions.',
                                'ref':client_po,
                                'order_line': line.id,
                                'invoice_id': False,
                                'state': 'draft',
                                }
                            self.env['sale.commission'].create(vals)

                    comm_lines = comm.sudo().search([('order_id','=',order.id),('pmt_id','=',False),('invoice_id','=',False),])
                if not comm_lines:
                    raise UserError(_('Commission records not created.'))               
                invoice_vals['invoice_line_ids'] = [
                    (0, 0, line._prepare_comm_invoice_line())
                    for line in comm_lines
                ]
                invoice_vals_list.append(invoice_vals)
                # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
                # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
                moves = self.env['account.move'].sudo().with_context(default_type='in_invoice').create(invoice_vals_list)
                move_id = moves and moves[0] and moves[0].id or None           
                order.comm_inv_paid = False
                order.comm_inv_id = move_id
                if move_id:
                    for line in comm_lines:
                        line.invoice_id = move_id  
            else:
                raise UserError(_('The order must be shipped and paid before creating a commissions invoice.'))
        return moves