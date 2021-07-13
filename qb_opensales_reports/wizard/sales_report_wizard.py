from odoo import api, fields, models
from odoo.tools.misc import get_lang

class SalesReportWizard(models.TransientModel):
    _name = "sales.report.wizard"
    _description = "Sales Report Wizard"
    
    company_id = fields.Many2one("res.company",string="Company")
    date_from = fields.Date("Date From", required=False)
    date_to = fields.Date("Date To", required=False)
    showroom = fields.Many2many("crm.team",'sales_crm_rel_transient', 'sales_report_id', 'crm_team_id', string="Showroom")
    sale_ids = fields.Many2many("sale.order",'sales_report_rel_transient', 'sales_report_id', 'sale_order_id', string="Sales")
    print_selected = fields.Boolean("Print Selected?")
    
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['company_id','date_from', 'date_to', 'showroom','sale_ids','print_selected'])[0]
        #used_context = self._build_contexts(data)
        #data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        #return self.with_context(discard_logo_check=True)._print_report(data)
        return self.env.ref('qb_opensales_reports.action_report_opensales').report_action(self, data=data)