from odoo import api, fields, models
from odoo.tools.misc import get_lang

class WIPReportWizard(models.TransientModel):
    _name = "wip.report.wizard"
    _description = "WIP Report Wizard"
    
    workcenter_id = fields.Many2many("mrp.workcenter",string="Workcenters")
    user_id = fields.Many2one("res.users",string="Responsible")
    
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['user_id', 'workcenter_id'])[0]
        #used_context = self._build_contexts(data)
        #data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        #return self.with_context(discard_logo_check=True)._print_report(data)
        return self.env.ref('qb_wip_report.action_wip_report').report_action(self, data=data)