# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BarcodeMRPLabelsWiz(models.TransientModel):
    _name = "barcode.mrp.labels.wiz"
    _description = 'Barcode MRP Labels Wizard'

    product_barcode_ids = fields.One2many('barcode.mrp.labels.wiz.line', 'label_id', 'Product Barcode')
    
    @api.model
    def default_get(self, fields):
        res = super(BarcodeMRPLabelsWiz, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        production_ids = self.env['mrp.production'].browse(active_ids)
        
        barcode_order_lines = []
        for mrp in production_ids:
            sale_order_id = mrp and mrp.sale_order_id or None
            barcode_order_lines.append((0,0, {
                'label_id' : self.id,
                'product_id' : mrp.product_id.id, 
                'qty' : mrp.product_qty or 1,
                'sale_id': sale_order_id and sale_order_id.id or None,
                'production_id': mrp.id,
                'company_id': mrp.company_id.id,
            }))
        res.update({
            'product_barcode_ids': barcode_order_lines
        })
        return res

    def print_barcode_labels(self):
        self.ensure_one()
        [data] = self.read()
        #barcode_config = \
        #            self.env.ref('bi_dynamic_barcode_labels.barcode_labels_config_data')
        #if not barcode_config.barcode_currency_id or not barcode_config.barcode_currency_position:
        #    raise UserError(_('Barcode Configuration fields are not set in data (Inventory -> Settings -> Barcode Configuration)'))
        data['barcode_labels'] = data['product_barcode_ids']
        barcode_lines = self.env['barcode.mrp.labels.wiz.line'].browse(data['barcode_labels'])
        datas = {
             'ids': [1],
             'model': 'barcode.mrp.labels.wiz',
             'form': data
        }
        return self.env.ref('bi_dynamic_barcode_labels.printed_mrp_order_barcode_labels').report_action(barcode_lines, data=datas)


class BarcodeMRPLabelsLine(models.TransientModel):
    _name = "barcode.mrp.labels.wiz.line"
    _description = 'Barcode MRP Labels Line'
    
    label_id = fields.Many2one('barcode.mrp.labels.wiz','Barcode labels')
    product_id = fields.Many2one('product.product','Product')
    production_id = fields.Many2one('mrp.production','MRP')
    qty = fields.Integer('Barcode Qty', default=1)
    sale_id = fields.Many2one('sale.order','Sale Order',store=True)
    label_text = fields.Text('Free Text')
    company_id = fields.Many2one('res.company','Company')
       
    @api.model
    def default_get(self, fields):
        res = super(BarcodeMRPLabelsLine, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        production_ids = self.env['mrp.production'].browse(active_ids)
        sale_id = production_ids and production_ids[0] and production_ids[0].sale_order_id and production_ids[0].sale_order_id.id or False
        res.update({'sale_id': sale_id})
        return res