from odoo import api, fields, models
from odoo.tools.misc import get_lang

class CompSalesReportWizard(models.TransientModel):
    _name = "comp.sales.report.wizard"
    _description = "Completed Sales Report Wizard"
    
    company_id = fields.Many2one("res.company",string="Company",required=True)
    date_from = fields.Date("Date From", required=False)
    date_to = fields.Date("Date To", required=False)
    showroom = fields.Many2many("crm.team",'sales_crm_rel_transient', 'sales_report_id', 'crm_team_id', string="Showroom")
    sale_ids = fields.Many2many("sale.order",'sales_report_rel_transient', 'sales_report_id', 'sale_order_id', string="Sales")
    print_selected = fields.Boolean("Print Selected?")
    print_excel = fields.Boolean("Print in Excel")
    sales_rep_id = fields.Many2one("res.partner",string="Sales Rep.") 
    
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['sales_rep_id','responsible_id','company_id','date_from', 'date_to', 'showroom','sale_ids','print_selected'])[0]
        #used_context = self._build_contexts(data)
        #data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        #return self.with_context(discard_logo_check=True)._print_report(data)
        print_excel = self.read(['print_excel'])[0]
        print_excel = 'print_excel' in print_excel and print_excel['print_excel'] or False
        if print_excel:
            return self.env.ref('qb_opensales_reports.action_report_compsales_xlsx').report_action(self, data=data)        
        else:
            return self.env.ref('qb_opensales_reports.action_report_compsales').report_action(self, data=data)

            
class SalesReportWizard(models.TransientModel):
    _name = "sales.report.wizard"
    _description = "Sales Report Wizard"
    
    company_id = fields.Many2one("res.company",string="Company",required=True)
    date_from = fields.Date("Date From", required=False)
    date_to = fields.Date("Date To", required=False)
    showroom = fields.Many2many("crm.team",'sales_crm_rel_transient', 'sales_report_id', 'crm_team_id', string="Showroom")
    sale_ids = fields.Many2many("sale.order",'sales_report_rel_transient', 'sales_report_id', 'sale_order_id', string="Sales")
    print_selected = fields.Boolean("Print Selected?")
    print_excel = fields.Boolean("Print in Excel")
    responsible_id = fields.Many2one("res.users",string="Responsible")
    sales_rep_id = fields.Many2one("res.partner",string="Sales Rep.") 
    
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['sales_rep_id','responsible_id','company_id','date_from', 'date_to', 'showroom','sale_ids','print_selected'])[0]
        #used_context = self._build_contexts(data)
        #data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        #return self.with_context(discard_logo_check=True)._print_report(data)
        print_excel = self.read(['print_excel'])[0]
        print_excel = 'print_excel' in print_excel and print_excel['print_excel'] or False
        if print_excel:
            return self.env.ref('qb_opensales_reports.action_report_opensales_xlsx').report_action(self, data=data)        
        else:
            return self.env.ref('qb_opensales_reports.action_report_opensales').report_action(self, data=data)