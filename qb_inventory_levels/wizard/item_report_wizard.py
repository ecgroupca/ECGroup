from odoo import api, fields, models
from odoo.tools.misc import get_lang

            
class InventoryLevelsReportWizard(models.TransientModel):
    _name = "inventory.levels.report.wizard"
    _description = "Inventory Levels Report Wizard"
    
    category_ids = fields.Many2many("product.category",'invreport_cat_rel_transient', 'inv_report_id', 'categ_id', string="Categories")
    
    def print_report(self):
        self.ensure_one()
        data = {}
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['category_ids'])[0]
        return self.env.ref('qb_inventory_levels.action_report_inventory_levels_xlsx').report_action(self, data=data)