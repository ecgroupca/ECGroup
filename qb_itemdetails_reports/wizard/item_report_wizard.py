from odoo import api, fields, models
from odoo.tools.misc import get_lang

            
class itemReportWizard(models.TransientModel):
    _name = "item.report.wizard"
    _description = "Item Report Wizard"
    
    company_id = fields.Many2one("res.company",string="Company",required=True)
    date_from = fields.Date("Date From", required=False)
    date_to = fields.Date("Date To", required=False)
    showroom = fields.Many2many("crm.team",'item_crmteam_rel_transient', 'item_report_id', 'crm_team_id', string="Showroom")
    category_ids = fields.Many2many("product.category",'itemreport_cat_rel_transient', 'item_report_id', 'categ_id', string="Categories")
    print_excel = fields.Boolean("Print in Excel")
    responsible_id = fields.Many2one("res.users",string="Responsible")
    
    def print_report(self):
        self.ensure_one()
        fields = ['category_ids',
           'responsible_id',
           'company_id',
           'date_from',
           'date_to',
           'showroom'
        ]
        
        [data] = self.read(fields)
        
        datas = {
            'ids': [1],
            'model': 'item.report.wizard',
            'form': data,
        }

        print_excel = self.read(['print_excel'])
        print_excel = print_excel.get('print_excel',False)
        
        if print_excel:
            return self.env.ref('qb_itemdetails_reports.action_report_itemdetails_xlsx').report_action(self, data=datas)        
        else:
            return self.env.ref('qb_itemdetails_reports.action_report_itemdetails').report_action(self, data=datas)