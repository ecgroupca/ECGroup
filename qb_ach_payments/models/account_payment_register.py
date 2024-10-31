# Copyright 2023 Quickbeam, LLC - Adam O'Connor <aoconnor@quickbeamllc.com>  
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models



class AccountMove(models.Model):
    _inherit = 'account.move'

    purchase_id = fields.Many2one('purchase.order', readonly=False,)
                
class ResBank(models.Model): 
    _inherit = "res.bank"
    
    bic = fields.Char('Routing ID')
    
class AccountPayment(models.Model):
    _inherit = "account.payment"
    
    routing_number = fields.Char(related='journal_id.bank_id.bic')
    account_number = fields.Char(related='journal_id.bank_acc_number')

    def create_ach(self):
        for rec in self:
            #create an object to store the ACH data
            if rec.payment_method_id and rec.payment_method_id.code == 'ACH':
                if rec.payment_type == 'outbound':
                    self.env['ach.payment'].create({
                        'payment_id': rec.id,
                        'message_text': 'Some msg text!', 
                        'state': 'draft'
                    })            