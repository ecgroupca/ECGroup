from odoo import api, fields, models
from odoo.tools.misc import get_lang

            
class InventoryLevelsReportWizard(models.TransientModel):
    _name = "inventory.levels.report.wizard"
    _description = "Inventory Levels Report Wizard"
    
    company_id = fields.Many2one("res.company",string="Company",required=True)
    category_ids = fields.Many2many("product.category",'invreport_cat_rel_transient', 'inv_report_id', 'categ_id', string="Categories")
    print_excel = fields.Boolean("Print in Excel")
    responsible_id = fields.Many2one("res.users",string="Responsible")
    
    def print_report(self):
        self.ensure_one()
        data = {}
        #data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['category_ids','responsible_id','company_id','date_from', 'date_to', 'showroom'])[0]
        print_excel = self.read(['print_excel'])[0]
        print_excel = 'print_excel' in print_excel and print_excel['print_excel'] or False
        if print_excel:
            return self.env.ref('qb_inventory_levels.action_report_inventory_levels_xlsx').report_action(self, data=data)        
        else:
            return self.env.ref('qb_inventory_levels.action_report_inventory_levels').report_action(self, data=data)