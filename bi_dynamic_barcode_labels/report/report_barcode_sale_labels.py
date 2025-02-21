# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class DynamicBarcodeSaleLabelsParser(models.AbstractModel):
	_name = 'report.bi_dynamic_barcode_labels.sale_dynamic_barcode_labels'
	_description = "Sale Product variant barcode labels Report"

	def _get_barcode_details_info(self):
		barcode_config = \
			self.env.ref('bi_dynamic_barcode_labels.barcode_labels_config_data')
        return {
            'barcode_type': 'EAN13',
            'barcode_width': 120,
            'barcode_height': 25,
            'barcode_currency_id': 1,
            'barcode_currency_position': 'before',
            }

	@api.model
	def _get_report_values(self, docids, data=None):
		barcode_labels_report = self.env['ir.actions.report']._get_report_from_name('bi_dynamic_barcode_labels.sale_dynamic_barcode_labels')
        barcode_labels = 'form' in data
        barcode_labels = barcode_labels and 'barcode_labels' in data or []
        logger.info('Data: ' + str(data))
        
        if barcode_labels:
            barcode_labels = self.env['barcode.product.labels.wiz.line'].browse(barcode_labels)
            
        return {
            'doc_ids': barcode_labels,
            'doc_model': barcode_labels_report.model,
            'docs': barcode_labels,
            'data': data,
            'get_barcode_details_info': self._get_barcode_details_info(),
            }
