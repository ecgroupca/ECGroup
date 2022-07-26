# -*- coding: utf-8 -*-

import time

from odoo import models, fields, api, _
from odoo.exceptions import UserError, Warning

class ManufacturingProductionRequest(models.Model):
    _name = 'manufacturing.request.custom'
    _description = 'Manufacturing Production Request '
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'number'
    _order = 'id desc'

    number = fields.Char(
        string="Number",
        readonly=True
    )
    custom_product_template_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        copy=True,
        domain="[('bom_ids', '!=', False), ('bom_ids.active', '=', True), ('bom_ids.type', '=', 'normal'), ('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', custom_company_id)]"
    )
    custom_company_id = fields.Many2one(
        'res.company', 
        string='Company',
        default=lambda self: self.env.user.company_id,
        required=True,
        copy=True
    )
    state = fields.Selection(
        [('a_draft','New'),
         ('b_confirm','Confirmed'),
         ('c_validate','Approved'),
         ('d_manufacturing_created','Manufacturing Order Created'),
         ('cancel','Cancelled'),
        ],
        tracking=True,
        default='a_draft',
        string='State',
        copy=True
    )
    custom_user_id = fields.Many2one(
        'res.users', 
        string='Responsible User',
        default=lambda self: self.env.user,
        required=True,
        copy=True 
    )
    custom_bom_id = fields.Many2one(
        'mrp.bom',
        required=True,
        string='Bill of Material',
        copy=True,
        domain="""[
        '&',
            '|',
                ('company_id', '=', False),
                ('company_id', '=', custom_company_id),
            '&',
                '|',
                    ('product_id','=',custom_product_template_id),
                    '&',
                        ('product_tmpl_id.product_variant_ids','=',custom_product_template_id),
                        ('product_id','=',False),
        ('type', '=', 'normal')]""",
    )
    custom_description = fields.Text(
        string='Description',
        copy=True
    )
    custom_product_uom_id = fields.Many2one(
        'uom.uom', 
        string='Product Unit of Measure',
        required=True,
        copy=True
    )
    custom_product_qty = fields.Float(
        'Quantity To Produce',
        default=1.0, 
        digits='Product Unit of Measure',
        required=True,
        copy=True
    )
    create_date = fields.Date(
        string="Request Date",
        default=fields.date.today(),
        copy=True
    )
    end_date = fields.Datetime(
        string="Deadline",
        copy=True
    )
    custom_manufacturing_order_id = fields.Many2one(
        'mrp.production',
        string="Manufacturing Order",
        copy=True
    )
    confirm_by = fields.Many2one(
        'res.users',
        string="Confirmed by",
        readonly=True,
        copy=False
    )
    confirm_date = fields.Date(
        string="Confirmed Date",
        readonly=True,
        copy=False
    )
    approve_by = fields.Many2one(
        'res.users',
        string="Approved by",
        readonly=True,
        copy=False
    )
    approve_date = fields.Date(
        string="Approved Date",
        readonly=True,
        copy=False
    )
    manufacturing_create_by = fields.Many2one(
        'res.users',
        string="Manufacturing Created by",
        readonly=True,
        copy=False
    )
    manufacturing_date = fields.Date(
        string="Manufacturing Created Date",
        readonly=True,
        copy=False
    )
    custom_date_start_wo = fields.Datetime(
        'Plan From',
        copy=True
    )
    notes = fields.Text(
        string='Internal Notes',
        copy=True,
    )


    def custom_action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
    
    def custom_action_reset_draft(self):
        for rec in self:
            rec.state = 'a_draft'

    def custom_action_confirm(self):
        for rec in self:
            rec.state = 'b_confirm'
            rec.confirm_by = self.env.user
            rec.confirm_date = fields.date.today()

    def custom_action_validate(self):
        for rec in self:
            rec.state = 'c_validate'
            rec.approve_by =self.env.user
            rec.approve_date = fields.date.today()

    def custom_manufacturing_order_create(self):
        for rec in self:
            mrp_vals = {
                'product_id': rec.custom_product_template_id.id,
                'product_qty': rec.custom_product_qty,
                'product_uom_id': rec.custom_product_uom_id.id,
                'bom_id': rec.custom_bom_id.id,
                'origin':rec.number,
                'date_deadline':rec.end_date,
                'date_planned_start':rec.custom_date_start_wo,
                'custom_request_id':rec.id,
            }
            new_line = self.env['mrp.production'].new(mrp_vals)
            new_line._onchange_product_id()
            new_line._onchange_move_raw()
            mrp_vals_dict = self.env['mrp.production']._convert_to_write({
                    name: new_line[name] for name in new_line._cache
                })
            mrp_id = self.env['mrp.production'].create(mrp_vals_dict)
            rec.custom_manufacturing_order_id = mrp_id.id
            rec.state = 'd_manufacturing_created'
            rec.manufacturing_date = fields.date.today()
            rec.manufacturing_create_by = self.env.user
        action = self.env.ref('mrp.mrp_production_action')
        result = action.sudo().read()[0]
        result['domain'] = [('custom_request_id', '=', self.id)]
        return result

    @api.model
    def create(self, vals):
        vals['number'] = self.env['ir.sequence'].next_by_code('manufacturing.request.custom')
        return super(ManufacturingProductionRequest, self).create(vals)

    def unlink(self):
        for request in self:
            if request.state not in ('a_draft', 'cancel'):
                raise UserError(_('You cannot delete MRP Production Request is not draft or cancelled.'))
        return super(ManufacturingProductionRequest, self).unlink()

    def action_view_mrp_production(self):
        self.ensure_one()
        action = self.env.ref('mrp.mrp_production_action').sudo().read()[0]
        action['domain'] = [('custom_request_id', '=', self.id)]
        return action

    @api.onchange('custom_product_template_id')
    def on_change_product_custom(self):
        self.custom_product_uom_id = self.custom_product_template_id.uom_id.id
