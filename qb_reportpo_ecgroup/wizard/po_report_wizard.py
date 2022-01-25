from odoo import api, fields, models
from odoo.tools.misc import get_lang

class VendorPOReportWizard(models.TransientModel):
    _name = "vendor.po.report.wizard"
    _description = "Vendor PO Report Wizard"
    
    date_from = fields.Date("Date From", required=False)
    date_to = fields.Date("Date To", required=False)
    partner_ids = fields.Many2many("res.partner",'po_report_vendor_rel_transient', 'vendor_report_id', 'vendor_id', string="Vendor")
    company_id = fields.Many2one("res.company",string="Company",required=True)
    #showroom = fields.Many2many("crm.team",'shipping_crm_rel_transient', 'shipping_report_id', 'crm_team_id', string="Showroom")
    #stock_move_ids = fields.Many2many("stock.move",'shipping_stock_rel_transient', 'shipping_report_id', 'stock_move_id', string="Stock Moves")
    #print_selected = fields.Boolean("Print Selected?")
    #hide_print_selected = fields.Boolean("Hide Print Selected")
    
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['company_id','date_from', 'date_to', 'partner_ids'])[0]
        #used_context = self._build_contexts(data)
        #data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        #return self.with_context(discard_logo_check=True)._print_report(data)
        return self.env.ref('qb_reportpo_ecgroup.action_report_open_po').report_action(self, data=data)