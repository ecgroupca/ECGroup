# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    custom_request_id = fields.Many2one(
        'manufacturing.request.custom',
        string='Manufacturing Request',
        readonly=True,
        copy=False,
    )

    @api.onchange('product_id', 'picking_type_id', 'company_id')
    def onchange_product_id(self):
        if self.custom_request_id.custom_bom_id:
            self.bom_id = self.custom_request_id.custom_bom_id.id
            self.product_qty = self.custom_request_id.custom_product_qty
            self.product_uom_id = self.custom_request_id.custom_product_uom_id.id
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
