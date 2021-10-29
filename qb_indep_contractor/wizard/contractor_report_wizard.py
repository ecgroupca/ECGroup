from odoo import api, fields, models
from odoo.tools.misc import get_lang


class IndepContractorWizard(models.AbstractModel):

    _name = "indep.contractor.wizard"
    _description = 'Independent Contractor Report'
    
    vendor_id = fields.Many2one('res.partner',string='Vendor') 
    date_from = fields.Date("Date From", required=True)
    date_to = fields.Date("Date To", required=True)
    tax_id = fields.Char(string='Tax ID', related ='vendor_id.vat')
                
        
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['tax_id','billing_address_id','vendor_id','date_from','date_to'])[0]
        return self.env.ref('qb_indep_contractor.action_report_indep_contractor').report_action(self, data=data)