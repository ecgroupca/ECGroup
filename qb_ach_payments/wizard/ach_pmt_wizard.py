from odoo import api, fields, models
from odoo.tools.misc import get_lang
from odoo.exceptions import ValidationError, Warning

            
class SendACHWizard(models.TransientModel):
    _name = "send.ach.wizard"
    _description = "Send ACH Wizard"
    
    company_id = fields.Many2one("res.company",string="Company",required=True)
    responsible_id = fields.Many2one("res.users",string="Responsible")
    recipient_id = fields.Many2one("",string="Recipient")
    amount = fields.Monetary('ACH Amount')
    currency_id = fields.Many2one('res.currency', string='Currency', 
        required=True, readonly=True, 
        states={'draft': [('readonly', False)]}, 
        default=lambda self: self.env.company.currency_id)  


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
                
    def cancel_ach(self):
        for ach in self:
            if ach.state == 'posted':
                ach.state = 'canceled'
        
    def create_ach(self):
        #create the ach text to send
        ach = """some edi text to create ach transaction
        """
        return ach
    
    def send_ach(self):
        for pmt in self:
            if pmt.state == 'posted':
                ach = pmt.create_ach()
                msg = 'Please confirm that you wish to send $%s to %s'%(pmt.amount,pmt.partner_id)
                raise Warning(msg)
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