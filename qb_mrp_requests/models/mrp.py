from odoo import api, fields, models, _
from collections import defaultdict
from odoo.exceptions import ValidationError,UserError


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'
    
    qty_available = fields.Float(
        'Qty Available',
        related='product_tmpl_id.qty_available'       
        )

    operation_id = fields.Many2one(
        required=True,
        tracking=True,
        )   
        

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    request_line_id = fields.Many2one(
        'manufacturing.request.line',
        string='Manufacturing Request',
        readonly=True,
        copy=False,
    )
  
    @api.onchange('product_id', 'picking_type_id', 'company_id')
    def onchange_product_id(self):
        if self.request_line_id.bom_id:
            self.bom_id = self.request_line_id.bom_id.id
            self.product_qty = self.request_line_id.product_uom_qty
            self.product_uom_id = self.request_line_id.product_uom.id
            
    def button_mark_done(self):
        res = super().button_mark_done()
        if res:
            self.mrp_production_request_id.state = 'repaired'
        return res
        
        
class ManufacturingRequestLine(models.Model):
    _name = "manufacturing.request.line"
    
    program = fields.Char('Program')
    
    subprogram = fields.Char('Sub-program')
    
    date_start_wo = fields.Date(
        'Plan From',
        tracking=True,
    )
    
    end_date = fields.Datetime(
        'Deadline',
        tracking=True,
    )
    
    product_id = fields.Many2one(
        'product.product', 
        string="Product",
        copy=True,
        required=True,
        tracking=True,
        )
        
    bom_id = fields.Many2one(
        'mrp.bom', 
        string="BoM",
        required=True,
        domain = "['|',('product_tmpl_id.product_variant_ids','=',product_id),('product_id','=',product_id)]",
        copy=True,
        tracking=True,
        )
        
    product_uom_qty = fields.Float(
        'Qty',
        required=True,
        copy=True, 
        tracking=True,        
        )
    
    product_uom = fields.Many2one(
        'uom.uom', 
        string="UoM",
        copy=True,
        tracking=True,
        required=True,
        )
    
    request_id = fields.Many2one(
        'manufacturing.request.custom',
        string="MRP Request",  
        )
        
    mrp_id = fields.Many2one(
        'mrp.production',
        string="MO Created",
        readonly=True,
        tracking=True,
        )
        
    def unlink(self):
        for line in self:
            if line.mrp_id and line.request_id.state not in ['a_draft','cancel']:
                raise UserError(_('Line cannot be deleted. It has an MO.'))
        return super(ManufacturingRequestLine, self).unlink()
   
    @api.onchange('product_id')
    def on_change_product(self):
        self.product_uom = self.product_id.uom_id
        
        
class ManufacturingRequestCustom(models.Model):
    _inherit = "manufacturing.request.custom"
    
    program = fields.Char('Program',tracking=True,)
    
    subprogram = fields.Char('Sub-program',tracking=True,)
    
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        tracking=True
        )
    
    line_ids = fields.One2many(
        'manufacturing.request.line',
        'request_id',
        string="Request Lines",
        ondelete="cascade",
        tracking=True,
        )
        
    mrp_ids = fields.One2many(
        'mrp.production',
        'custom_request_id',
        string="MOs",
        tracking=True,
        )
        
    state = fields.Selection(
        [
            ("a_draft", "Draft"),
            ("new", "New"),
            ("b_confirm", "Confirmed"),
            ("c_validate", "Validated"),
            ("programming", "Programming"),
            ("tooling", "Tooling"),
            ("ready", "Ready"),
            ("d_manufacturing_created", "MOs Created"),
            ("cancel", "Canceled"),
            ('done','Done'),
        ],
    default="a_draft",
    copy=False,
    tracking=True,
    )

    custom_product_template_id = fields.Many2one(
        required=False,
    )
    
    custom_product_uom_id = fields.Many2one(
        required=False,
    )
    
    custom_product_qty = fields.Float(
        required=False,
    )
    
    custom_bom_id = fields.Many2one(
        required=False,
        ) 

    create_date = fields.Date(
        tracking=True,
    )
    
    end_date = fields.Datetime(
        tracking=True,
    )
    
    confirm_by = fields.Many2one(
        tracking=True,
    )
    
    confirm_date = fields.Date(
        tracking=True,
    )
    
    approve_by = fields.Many2one(
        tracking=True,
    )
    
    approve_date = fields.Date(
        tracking=True,
    )
    
    custom_date_start_wo = fields.Datetime(
        tracking=True,
    )
    
    notes = fields.Text(
        tracking=True,
    ) 

    @api.onchange('subprogram')
    def onchange_subprogram(self):
        if self.subprogram:
            for line in self.line_ids:
                line.subprogram = self.subprogram

    @api.onchange('program')
    def onchange_program(self):
        if self.program:
            for line in self.line_ids:
                line.program = self.program

    @api.onchange('custom_date_start_wo')
    def onchange_date_start_wo(self):
        if self.custom_date_start_wo:
            for line in self.line_ids:
                line.date_start_wo = self.custom_date_start_wo                
    
    @api.onchange('end_date')
    def onchange_end_date(self):
        if self.end_date:
            for line in self.line_ids:
                line.end_date = self.end_date

    def action_programming(self):    
        for req in self:
            req.state = 'programming'
            
    def action_tooling(self):  
        for req in self:
            req.state = 'tooling'
            
    def action_ready(self):  
        for req in self:
            req.state = 'ready'
            
    def custom_manufacturing_order_create(self):
        for req in self:
            #loop through the req lines and aggregate products creating a new MO for each one
            mrp_created = {} #product_id: mrp_id
            """mrp_ids = req.mrp_ids
            for mrp in mrp_ids:
                bom_id = mrp.bom_id
                if bom_id and bom_id.id not in mrp_created:
                    mrp_created[line.bom_id.id] = mrp.id"""  
            for line in req.line_ids:              
                if line.product_id and line.bom_id and not line.mrp_id:
                    if line.bom_id.id not in mrp_created:
                        mrp_vals = {
                            'product_id': line.product_id.id,
                            'product_qty': line.product_uom_qty,
                            'product_uom_id': line.product_uom.id,
                            'bom_id': line.bom_id.id,
                            'origin': req.number,
                            'date_deadline': line.end_date,
                            'date_planned_start': line.date_start_wo,
                            'custom_request_id': req.id,
                            'request_line_id': line.id,
                        }
                        new_line = self.env['mrp.production'].new(mrp_vals)
                        new_line._onchange_product_id()
                        #new_line._onchange_bom_id()
                        new_line._onchange_move_raw()
                        mrp_vals_dict = self.env['mrp.production']._convert_to_write({
                                name: new_line[name] for name in new_line._cache
                            })
                        mrp_id = self.env['mrp.production'].create(mrp_vals_dict)
                        req.mrp_ids |= mrp_id
                        line.mrp_id = mrp_id
                        req.state = 'd_manufacturing_created'
                        req.manufacturing_date = fields.date.today()
                        req.manufacturing_create_by = self.env.user
                        mrp_created[line.bom_id.id] = new_line.id
                    else:
                        #raise exception stating that there is already an MO for that item 
                        raise ValidationError(
                            _("Duplicate BoM. A BoM can only appear on one request line.")
            ) 
        action = self.env.ref('mrp.mrp_production_action')
        result = action.sudo().read()[0]
        result['domain'] = [('custom_request_id', '=', self.id)]
        return result