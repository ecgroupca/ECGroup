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

        
class AccountPayment(models.Model):
    _inherit = "account.payment"

    
    sale_id = fields.Many2one(
        'sale.order',
        string = 'Sale Order', 
        compute = '_get_related'
    )
    
    @api.depends('invoice_line_ids')
    def _get_related(self):
        for payment in self:
            sale_id = False
            #1. loop through invoice_ids from payment
            for invoice in payment.invoice_ids:              
                #2. search for sale orders that have invoices on the payment list.
                for line in invoice.invoice_line_ids:
                    #3. loop through the invoice line's sale_line_ids
                    for sale_line in line.sale_line_ids:
                        sale_id = sale_line and sale_line.order_id or False
                        if sale_id:
                            #payment.sale_id = sale_id
                            break
                    if sale_id:
                        break
                if sale_id:
                    break
            payment.sale_id = sale_id
            
    def post(self):
        res = super(AccountPayment,self).post()
        #assign the pmt_id for each commission paid by this one.
        if res:
            for pmt in self:
                amt_due = 0
                amt_res = 0
                amt_inv = 0
                sale = pmt.sale_id                 
                if sale:                
                    for invoice in sale.invoice_ids:
                        if invoice.state=='posted':
                            amt_res += invoice.amount_residual
                            amt_inv += invoice.amount_total
                    sale.inv_bal_due = (sale.amount_total - amt_inv) + amt_res
                    if sale.inv_bal_due == 0:
                        sale.fully_paid_date = pmt.payment_date                    
                for invoice in pmt.invoice_ids:
                    commissions = self.env['sale.commission'].search([('invoice_id','=',invoice.id)])
                    comm_sale = self.env['sale.order'].search([('comm_inv_id','=',invoice.id)])
                    if invoice.amount_residual == 0:
                        comm_sale.comm_inv_paid = True
                    for comm in commissions:
                        comm.pmt_id = pmt
        
        return res