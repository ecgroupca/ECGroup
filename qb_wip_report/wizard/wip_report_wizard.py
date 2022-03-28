from odoo import api, fields, models
from odoo.tools.misc import get_lang

class WIPReportWizard(models.TransientModel):
    _name = "wip.report.wizard"
    _description = "WIP Report Wizard"
    
    workcenter_id = fields.Many2many("mrp.workcenter",string="Workcenters")
    user_id = fields.Many2one("res.users",string="Responsible")
    print_excel = fields.Boolean("Print in Excel")
    
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['user_id', 'workcenter_id'])[0]
        print_excel = self.read(['print_excel'])[0]
        print_excel = 'print_excel' in print_excel and print_excel['print_excel'] or False
        if print_excel:
            return self.env.ref('qb_wip_report.action_wip_report_xlsx').report_action(self, data=data)  
        else:
            return self.env.ref('qb_wip_report.action_wip_report').report_action(self, data=data)