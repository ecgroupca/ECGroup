# Copyright 2019 Elico Corp, Dominique K. <dominique.k@elico-corp.com.sg>
# Copyright 2019 Ecosoft Co., Ltd., Kitti U. <kittiu@ecosoft.co.th>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResBank(models.Model): 
    _inherit = "res.bank"
    
    bic = fields.Char('Routing ID')
    
class AccountPayment(models.Model):
    _inherit = "account.payment"
    
    routing_number = fields.Char(related='journal_id.bank_id.bic')
    account_number = fields.Char(related='journal_id.bank_acc_number')
