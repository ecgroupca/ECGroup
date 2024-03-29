# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BarcodeSaleLabelsWiz(models.TransientModel):
    _name = "barcode.sale.labels.wiz"
    _description = 'Barcode Product Labels Wizard'

    product_barcode_ids = fields.One2many('barcode.sale.labels.wiz.line', 'label_id', 'Product Barcode')
    
    @api.model
    def default_get(self, fields):
        res = super(BarcodeSaleLabelsWiz, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        sale_order_ids = self.env['sale.order'].browse(active_ids)
        barcode_order_lines = []
        for order in sale_order_ids:
            for line in order.order_line:
                if line.product_id and line.product_id.type != 'service':
                    barcode_order_lines.append((0,0, {
                        'label_id' : self.id,
                        'product_id' : line.product_id.id, 
                        'qty' : line.product_uom_qty or 1,
                        'sale_id': order.id,
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
        barcode_lines = self.env['barcode.sale.labels.wiz.line'].browse(data['barcode_labels'])
        datas = {
             'ids': [1],
             'model': 'barcode.sale.labels.wiz',
             'form': data
        }
        return self.env.ref('bi_dynamic_barcode_labels.printed_sale_order_barcode_labels_id').report_action(barcode_lines, data=datas)


class BarcodeSaleLabelsLine(models.TransientModel):
    _name = "barcode.sale.labels.wiz.line"
    _description = 'Barcode Product Labels Line'
    
    label_id = fields.Many2one('barcode.sale.labels.wiz','Barcode labels')
    product_id = fields.Many2one('product.product','Product')
    qty = fields.Integer('Barcode Qty', default=1)
    sale_id = fields.Many2one('sale.order','Sale Order',store=True)
    label_text = fields.Text('Free Text')
       
    @api.model
    def default_get(self, fields):
        res = super(BarcodeSaleLabelsLine, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        sale_order_ids = self.env['sale.order'].browse(active_ids)
        sale_id = sale_order_ids and sale_order_ids[0] and sale_order_ids[0].id or False
        res.update({'sale_id': sale_id})
        return res
