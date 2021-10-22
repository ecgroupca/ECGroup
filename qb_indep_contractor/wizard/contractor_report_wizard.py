from odoo import api, fields, models
from odoo.tools.misc import get_lang


class IndepContractorWizard(models.AbstractModel):

    _name = "indep.contractor.wizard"
    _description = 'Independent Contractor Report'
    
    vendor_id = fields.Many2one('res.partner',string='Vendor') 
    date_from = fields.Date("Date From", required=True)
    date_to = fields.Date("Date To", required=True)
    tax_id = fields.Char(string='Tax ID', related ='vendor_id.vat')
    total_paid = fields.Float(string='Total Paid', 
        computed = '_get_billing_total_paid',
        )         
    billing_address_id = fields.Many2one('res.partner',
        computed = '_get_billing_total_paid',
        string='Billing Address'
        ) 
            
    @api.depends('date_from','date_to')
    def _get_billing_total_paid(self):
        for indep in self:
            vendor_id = indep.vendor_id
            date_from = indep.date_from
            date_to = indep.date_to
            indep.total_paid = 0
            import pdb;pdb.set_trace()
            indep.billing_address_id = self.env['res.partner'].address_get(['invoice'])['invoice']
            if indep.billing_address_id:
                #search for all paid vendor bills for this billing address_get
                bills = self.env['account.move'].search([('partner_id','=',indep.billing_address_id)])
                total_paid = 0
                for bill in bills:
                    if bill.state == 'posted':
                        total_paid += bill.amount_total - bill.amount_residual
                indep.total_paid = total_paid
                
        
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['tax_id','billing_address_id','vendor_id','date_from','date_to'])[0]
        return self.env.ref('qb_indep_contractor.action_report_indep_contractor').report_action(self, data=data)