from odoo import api, fields, models
import datetime

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    needs_ten_ninety_nine = fields.Boolean("Needs 1099")
    total_paid_current_year = fields.Float(string='Total Paid Current Year', 
        compute = '_get_billing_total_paid',
        )         
    billing_address_id = fields.Many2one('res.partner',
        compute = '_get_billing_total_paid',
        string='Billing Address'
        ) 
       
    @api.depends('needs_ten_ninety_nine')
    def _get_billing_total_paid(self):
        for indep in self:
            indep.total_paid_current_year = 0
            now = datetime.datetime.now()
            date = now.date()
            year = date.strftime("%Y")
            bill_address = self.env['res.partner'].address_get(['invoice'])['invoice']
            indep.billing_address_id = bill_address and bill_address.id or None
            if indep.billing_address_id:
                #search for all paid vendor bills for this billing address_get
                bills = self.env['account.move'].search([('type','=''in_invoice'),('date','>=',year + '-01-01 00:00:00'),('date','<=',year + '-12-31 23:59:59'),('partner_id','=',indep.billing_address_id.id)])
                total_paid = 0
                for bill in bills:
                    if bill.state == 'posted':
                        total_paid += bill.amount_total - bill.amount_residual
                indep.total_paid_current_year = total_paid
                           
                
            
        
         