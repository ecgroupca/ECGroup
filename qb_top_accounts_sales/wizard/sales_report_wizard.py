from odoo import api, fields, models
from odoo.tools.misc import get_lang

class TopSalesWizard(models.TransientModel):
    _name = "top.account.sales.wiz"
    _description = "Top Sales Wizard"
    
    company_id = fields.Many2one("res.company",string="Company",required=False)
    date_from = fields.Date("Date From", required=False)
    date_to = fields.Date("Date To", required=False)
    group_showrooms = fields.Boolean("Group by Showroom")
    top_clients = fields.Float("Number of Top Clients",required=True,help="Type a number here for the number of top clients")
    
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['group_showrooms','top_clients','company_id','date_from', 'date_to'])[0]
        return self.env.ref('qb_top_accounts_sales.action_report_top_sales').report_action(self, data=data)