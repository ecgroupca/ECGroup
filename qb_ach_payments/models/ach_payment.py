# Copyright 2023 Quickbeam, LLC - Adam O'Connor <aoconnor@quickbeamllc.com>  
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models
from odoo.exceptions import ValidationError, Warning

    
class ACHPayment(models.Model):
    _name = "ach.payment"
    _description = """ACH Payments"""
    
    payment_id = fields.Many2one('account.payment',string='ACH Payment')
    name = fields.Char(related='payment_id.name', string='Name')
    payment_date = fields.Date(related='payment_id.payment_date', string='Date')
    company_id = fields.Many2one(related='payment_id.company_id', string='Company')
    journal_id = fields.Many2one(related='payment_id.journal_id', string='Journal')
    partner_id = fields.Many2one(related='payment_id.partner_id', string='Payee')
    amount = fields.Monetary(related='payment_id.amount')
    currency_id = fields.Many2one('res.currency', string='Currency', 
        required=True, readonly=True, 
        states={'draft': [('readonly', False)]}, 
        default=lambda self: self.env.company.currency_id)
    ach_pmt_date = fields.Date(string='Date', 
        default=fields.Date.context_today, 
        required=True, readonly=True, 
        states={'draft': [('readonly', False)]}, 
        copy=False, tracking=True)
    message_text = fields.Text('Message Text')
    state = fields.Selection([('draft', 'Draft'), 
        ('posted', 'Validated'), 
        ('sent', 'Sent')], 
        readonly=True, default='draft', 
        copy=False, string="Status")
        
    def bank_auth(self):
        error = ''
        return error
       
    def bank_send(self):
        error = ''
        return error
        
    def validate_ach(self):
        for ach in self:
            if ach.state == 'draft':
                ach.state = 'posted'
                
    def reset_ach(self):
        for ach in self:
            if ach.state == 'posted':
                ach.state = 'draft'
        
    def create_ach(self):
        #create the ach text to send
        ach = """some edi text to create ach transaction
        """
        return ach
    
    def send_ach(self):
        for pmt in self:
            if pmt.state == 'posted':
                ach = pmt.create_ach()
                auth_error = pmt.bank_auth()
                #now that you've authenticated, 
                #send the message (one at a time).
                send_error = pmt.bank_send()
                #return error
                pmt.state = 'sent'
            else:
                #raise exception that it must be in Validated status.
                msg = "ACH Must be Validated."
                raise ValidationError(msg)
                
        