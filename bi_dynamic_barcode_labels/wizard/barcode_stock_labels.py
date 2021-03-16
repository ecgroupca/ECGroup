# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BarcodeStockLabelsWiz(models.TransientModel):
    _name = "barcode.stock.labels.wiz"
    _description = 'Barcode Product Labels Wizard'

    product_barcode_ids = fields.One2many('barcode.stock.labels.wiz.line', 'label_id', 'Product Barcode')

    @api.model
    def default_get(self, fields):
        res = super(BarcodeStockLabelsWiz, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        stock_picking_ids = self.env['stock.picking'].browse(active_ids)
        barcode_order_lines = []
        for order in stock_picking_ids:
            for line in order.move_ids_without_package:
                barcode_order_lines.append((0,0, {
                    'label_id' : self.id,
                    'product_id' : line.product_id.id, 
                    'qty' : line.product_uom_qty or 1,
                }))
        res.update({
            'product_barcode_ids': barcode_order_lines
        })
        return res

    def print_barcode_labels(self):
        self.ensure_one()
        [data] = self.read()
        barcode_config = \
                    self.env.ref('bi_dynamic_barcode_labels.barcode_labels_config_data')
        if not barcode_config.barcode_currency_id or not barcode_config.barcode_currency_position:
            raise UserError(_('Barcode Configuration fields are not set in data (Inventory -> Settings -> Barcode Configuration)'))
        data['barcode_labels'] = data['product_barcode_ids']
        barcode_lines = self.env['barcode.stock.labels.wiz.line'].browse(data['barcode_labels'])
        datas = {
             'ids': [1],
             'model': 'barcode.stock.labels.wiz',
             'form': data
        }
        return self.env.ref('bi_dynamic_barcode_labels.printed_stock_picking_barcode_labels_id').report_action(barcode_lines, data=datas)


class BarcodeStockLabelsLine(models.TransientModel):
    _name = "barcode.stock.labels.wiz.line"
    _description = 'Barcode Product Labels Line'
    
    label_id = fields.Many2one('barcode.stock.labels.wiz', 'Barcode labels')
    product_id = fields.Many2one('product.product',' Product')
    qty = fields.Integer('Barcode', default=1)
