# Copyright 2021 Quickbeam, LLC - Adam O'Connor <aoconnor@quickbeamllc.com>  
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResBank(models.Model): 
    _inherit = "res.bank"
    
    bic = fields.Char('Routing ID')
    
class AccountPayment(models.Model):
    _inherit = "account.payment"
    
    routing_number = fields.Char(related='journal_id.bank_account_id.aba_routing')
    account_number = fields.Char(related='journal_id.bank_acc_number')
