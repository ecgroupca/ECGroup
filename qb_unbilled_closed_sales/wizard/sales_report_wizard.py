from odoo import api, fields, models
from odoo.tools.misc import get_lang

class UnbilledSalesWizard(models.TransientModel):
    _name = "unbilled.sales.wizard"
    _description = "Unbilled Sales Wizard"
    
    company_id = fields.Many2one("res.company",string="Company",required=True)
    date_from = fields.Date("Date From", required=False)
    date_to = fields.Date("Date To", required=False)
    showroom = fields.Many2many("crm.team",string="Showroom")
    
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['company_id','date_from', 'date_to', 'showroom'])[0]
        #used_context = self._build_contexts(data)
        #data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        #return self.with_context(discard_logo_check=True)._print_report(data)
        return self.env.ref('qb_unbilled_closed_sales.action_report_unbilled_sales').report_action(self, data=data)