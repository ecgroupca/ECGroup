# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'


    barcode_currency_id = fields.Many2one('res.currency')
    barcode_currency_position = fields.Selection([
        ('after', _('After')),
        ('before', _('Before')),
    ])



class BarcodeConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    default_purchase_deposit_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Purchase Deposit Product",
        default_model="purchase.advance.payment.inv",
        domain=[("type", "=", "service")],
        help="Default product used for payment advances.",
    )

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
    barcode_currency_id = fields.Many2one('res.currency',readonly=False,related='company_id.barcode_currency_id')
    barcode_currency_position = fields.Selection([
        ('after', _('After')),
        ('before', _('Before')),
    ],readonly=False,related='company_id.barcode_currency_position', string='Position')
    hide_price = fields.Boolean(string="hide price")



    @api.model
    def default_get(self, fields):
        settings = super(BarcodeConfigSettings, self).default_get(fields)
        settings.update(self.get_barcode_label_config(fields))
        return settings

    @api.model
    def get_barcode_label_config(self, fields):
        barcode_config = \
                    self.env.ref('bi_dynamic_barcode_labels.barcode_labels_config_data')

        return {
            'barcode_type': barcode_config.barcode_type,
            'barcode_width': barcode_config.barcode_width,
            'barcode_height': barcode_config.barcode_height,
            'label_width': barcode_config.label_width,
            'label_height': barcode_config.label_height,
            'hide_price' : barcode_config.hide_price,
        }


    def set_values(self):
        super(BarcodeConfigSettings, self).set_values()
        for rec in self:
            ICPSudo = rec.env['ir.config_parameter'].sudo()
            ICPSudo.set_param('bi_dynamic_barcode_labels.barcode_currency_position',rec.barcode_currency_position)
            ICPSudo.set_param('bi_dynamic_barcode_labels.barcode_currency_id',rec.barcode_currency_id.id)

        barcode_config = \
                    self.env.ref('bi_dynamic_barcode_labels.barcode_labels_config_data')
        vals = {
            'barcode_type': self.barcode_type,
            'barcode_width': self.barcode_width,
            'barcode_height': self.barcode_height,
            'label_width': self.label_width,
            'label_height': self.label_height,
            'hide_price' : self.hide_price,
        }


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
    ], string='Position')
    hide_price = fields.Boolean(string="hide price")
