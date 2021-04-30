from odoo import api, fields, models
from odoo.tools.misc import get_lang

class ShippingReportWizard(models.TransientModel):
    _name = "shipping.report.wizard"
    _description = "Shipping Report Wizard"
    
    date_from = fields.Date("Date From", required=False)
    date_to = fields.Date("Date To", required=False)
    showroom = fields.Many2many("crm.team",'shipping_crm_rel_transient', 'shipping_report_id', 'crm_team_id', string="Showroom")
    stock_move_ids = fields.Many2many("stock.move",'shipping_stock_rel_transient', 'shipping_report_id', 'stock_move_id', string="Stock Moves")
    print_selected = fields.Boolean("Print Selected?")
    
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'showroom','stock_move_ids','print_selected'])[0]
        #used_context = self._build_contexts(data)
        #data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        #return self.with_context(discard_logo_check=True)._print_report(data)
        return self.env.ref('shipping_reports.action_report_shipping').report_action(self, data=data)