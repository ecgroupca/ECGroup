from odoo import api, fields, models, _
from odoo.exceptions import UserError

        
class MRPWorkcenter(models.Model):
    _inherit = "mrp.workcenter"
    
    is_quality = fields.Boolean('Quality')
    
    
class MRPWorkorder(models.Model):
    _inherit = "mrp.workorder"
 
    def button_start(self):
        #check if the user is a quality user if this WO's workcenter is 'quality'
        if self.workcenter_id.is_quality:
            quality_group = self.env['res.groups'].search([('name','=','Quality Workcenter')])
            if quality_group:
                quality_user = self.env.user.id in quality_group.users.ids
                if not quality_user:
                    raise UserError(_("Quality WOs can only be started by manufacturing quality users."))                    
        return super(MRPWorkorder, self).button_start()