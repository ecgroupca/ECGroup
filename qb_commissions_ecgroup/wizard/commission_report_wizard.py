from odoo import api, fields, models
from odoo.tools.misc import get_lang

class CommissionReportWizard(models.TransientModel):
    _name = "commission.report.wizard"
    _description = "Commission Report Wizard"
    
    company_id = fields.Many2one("res.company",string="Company",required=True)
    date_from = fields.Date("Date From", required=True)
    date_to = fields.Date("Date To", required=True)
    remove_paid = fields.Boolean("Remove Paid Commissions")
    print_excel = fields.Boolean("Excel w/ Sheet For Each Showroom")
    print_excel_std = fields.Boolean("Print as Excel")
    showroom = fields.Many2many("crm.team",
       'commission_crm_rel_transient', 
       'commission_report_id', 
       'crm_team_id',
       string="Showroom"
       )
    
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['print_excel', 'print_excel_std','company_id','remove_paid','date_from', 'date_to', 'showroom'])[0]
        print_excel = self.read(['print_excel'])[0]
        print_excel = 'print_excel' in print_excel and print_excel['print_excel'] or False
        print_excel_std = self.read(['print_excel_std'])[0]
        print_excel_std = 'print_excel_std' in print_excel_std and print_excel_std['print_excel_std'] or False
        if print_excel or print_excel_std:
            return self.env.ref('qb_commissions_ecgroup.action_report_sale_commission_xlsx').report_action(self, data=data) 
        else:
            return self.env.ref('qb_commissions_ecgroup.action_report_sale_commission').report_action(self, data=data)