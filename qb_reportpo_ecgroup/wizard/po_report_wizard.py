from odoo import api, fields, models
from odoo.tools.misc import get_lang


class VendorPOReportWizard(models.TransientModel):
    _name = "vendor.po.report.wizard"
    _description = "Vendor PO Report Wizard"
    
    date_from = fields.Date("Date From", required=False)
    date_to = fields.Date("Date To", required=False)
    partner_ids = fields.Many2many("res.partner",'po_report_vendor_rel_transient', 'vendor_report_id', 'vendor_id', string="Vendor")
    company_id = fields.Many2one("res.company",string="Company",required=True)
    print_excel = fields.Boolean("Print in Excel")
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
        print_excel = self.read(['print_excel'])[0]
        print_excel = 'print_excel' in print_excel and print_excel['print_excel'] or False
        if print_excel:
            return self.env.ref('qb_reportpo_ecgroup.action_report_open_po_xlsx').report_action(self, data=data)        
        else:
            return self.env.ref('qb_reportpo_ecgroup.action_report_open_po').report_action(self, data=data)