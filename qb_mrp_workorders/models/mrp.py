from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
        
class MRPWorkcenter(models.Model):
    _inherit = "mrp.workcenter"
    
    is_quality = fields.Boolean('Quality')
    
    
class MRPWorkorder(models.Model):
    _inherit = "mrp.workorder"
    

    def button_start(self):
    
        self.ensure_one()
        # As button_start is automatically called in the new view
        if self.state in ('done', 'cancel'):
            return True

        if self.workcenter_id.is_quality:
            quality_group = self.env['res.groups'].search([('name','=','Quality Workcenter')])
            if quality_group:
                quality_user = self.env.user.id in quality_group.users.ids
                if not quality_user:
                    raise UserError(_("Quality workorders can only be started by quality users."))  
            
        if self.product_tracking == 'serial':
            self.qty_producing = 1.0
        else:
            self.qty_producing = self.qty_remaining

        self.env['mrp.workcenter.productivity'].create(
            self._prepare_timeline_vals(self.duration, datetime.now())
        )
        if self.production_id.state != 'progress':
            self.production_id.write({
                'date_start': datetime.now(),
            })
        if self.state == 'progress':
            return True
        start_date = datetime.now()
        vals = {
            'state': 'progress',
            'date_start': start_date,
        }
        if not self.leave_id:
            leave = self.env['resource.calendar.leaves'].create({
                'name': self.display_name,
                'calendar_id': self.workcenter_id.resource_calendar_id.id,
                'date_from': start_date,
                'date_to': start_date + relativedelta(minutes=self.duration_expected),
                'resource_id': self.workcenter_id.resource_id.id,
                'time_type': 'other'
            })
            vals['leave_id'] = leave.id
            return self.write(vals)
        else:
            if self.date_planned_start > start_date:
                vals['date_planned_start'] = start_date
            if self.date_planned_finished and self.date_planned_finished < start_date:
                vals['date_planned_finished'] = start_date
            return self.write(vals)