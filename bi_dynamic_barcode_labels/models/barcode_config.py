# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class BarcodeConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    barcode_type = fields.Selection([('EAN13', 'EAN13'),
                                     ('Code11', 'Code11'),
                                     ('Code128', 'Code128'),
                                     ('EAN8', 'EAN8'),
                                     ('Extended39', 'Extended39'),
                                     ('Extended93', 'Extended93'),
                                     ('QR', 'QR'),
                                     ('Standard39', 'Standard39'),
                                     ('Standard93', 'Standard93')],
                                     string='Type', default='EAN13')
    barcode_width = fields.Integer('Barcode Width')
    barcode_height = fields.Integer('Barcode Height')
    label_width = fields.Integer('Label Width(MM)')
    label_height = fields.Integer('Label Height(MM)')
    barcode_currency_id = fields.Many2one('res.currency')
    barcode_currency_position = fields.Selection([
        ('after', _('After')),
        ('before', _('Before')),
    ], string='Position', translate=True)

    @api.model
    def default_get(self, fields):
        settings = super(BarcodeConfigSettings, self).default_get(fields)
        #settings.update(self.get_barcode_label_config(fields))
        return settings

    """@api.model
    def get_barcode_label_config(self, fields):
        barcode_config = \
                    self.env.ref('bi_dynamic_barcode_labels.barcode_labels_config_data')
        return {
            'barcode_type': 'EAN13',
            'barcode_width': barcode_config.barcode_width,
            'barcode_height': barcode_config.barcode_height,
            'label_width': barcode_config.label_width,
            'label_height': barcode_config.label_height,
            'barcode_currency_id': barcode_config.barcode_currency_id.id,
            'barcode_currency_position': 'before',
        }"""

    def set_values(self):
        super(BarcodeConfigSettings, self).set_values()
        barcode_config = \
                    self.env.ref('bi_dynamic_barcode_labels.barcode_labels_config_data')
        vals = {
            'barcode_type': 'EAN13',
            'barcode_width': self.barcode_width,
            'barcode_height': self.barcode_height,
            'label_width': self.label_width,
            'label_height': self.label_height,
            'barcode_currency_id': self.barcode_currency_id.id,
            'barcode_currency_position': 'before',
        }
        # Update Paperformate
        #paper_formate = self.env['ir.model.data'].xmlid_to_object('bi_dynamic_barcode_labels.barcode_labels_report_paperformate')
        #paper_formate.page_height = self.label_height or 50
        #paper_formate.page_width = self.label_width  or 70

        barcode_config.write(vals)

class BarcodeLabelsConfig(models.Model):
    _name = 'barcode.labels.config'
    _description = 'Barcode Product Labels Configuration'

    barcode_type = fields.Selection([('EAN13', 'EAN13'),
                                     ('Code11', 'Code11'),
                                     ('Code128', 'Code128'),
                                     ('EAN8', 'EAN8'),
                                     ('Extended39', 'Extended39'),
                                     ('Extended93', 'Extended93'),
                                     ('QR', 'QR'),
                                     ('Standard39', 'Standard39'),
                                     ('Standard93', 'Standard93')], string='Type')

    barcode_width = fields.Integer('Barcode Width')
    barcode_height = fields.Integer('Barcode Height')
    label_width = fields.Integer('Label Width(MM)')
    label_height = fields.Integer('Label Height(MM)')
    barcode_currency_id = fields.Many2one('res.currency')
    barcode_currency_position = fields.Selection([
        ('after', _('After')),
        ('before', _('Before')),
    ], string='Position', translate=True)
