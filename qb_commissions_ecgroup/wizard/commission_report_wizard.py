from odoo import api, fields, models
from odoo.tools.misc import get_lang

class CommissionReportWizard(models.TransientModel):
    _name = "commission.report.wizard"
    _description = "Commission Report Wizard"
    
    date_from = fields.Date("Date From", required=True)
    date_to = fields.Date("Date To", required=True)
    showroom = fields.Many2many("crm.team",'commission_crm_rel_transient', 'commission_report_id', 'crm_team_id', string="Showroom")
    
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'showroom'])[0]
        #used_context = self._build_contexts(data)
        #data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        #return self.with_context(discard_logo_check=True)._print_report(data)
        return self.env.ref('qb_commissions_ecgroup.action_report_sale_commission').report_action(self, data=data)