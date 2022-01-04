from odoo import api, fields, models
from odoo.tools.misc import get_lang

            
class CheckbookReportWizard(models.TransientModel):
    _name = "checkbook.report.wizard"
    _description = "Checkbook Report Wizard"
    
    company_id = fields.Many2one("res.company",string="Company",required=True)
    date_from = fields.Date("Date From", required=False)
    date_to = fields.Date("Date To", required=False)
    print_excel = fields.Boolean("Print in Excel")
    responsible_id = fields.Many2one("res.users",string="Responsible")
    
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['responsible_id','company_id','date_from','date_to'])[0]
        #used_context = self._build_contexts(data)
        #data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        #return self.with_context(discard_logo_check=True)._print_report(data)
        print_excel = self.read(['print_excel'])[0]
        print_excel = 'print_excel' in print_excel and print_excel['print_excel'] or False
        if print_excel:
            return self.env.ref('qb_checkbook_register.report_checkbook_reg_xlsx').report_action(self, data=data)        
        else:
            return self.env.ref('qb_checkbook_register.report_checkbook_reg').report_action(self, data=data)