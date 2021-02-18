# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_destination_location(self):
        self.ensure_one()
        if not self.custom_dest_location_id:
            return super(SaleOrder, self)._get_destination_location()
        return self.custom_dest_location_id.id

    custom_dest_location_id = fields.Many2one('stock.location', 'Custom Destination Location', check_company=True,
                                              help="This is the custom destination location when you create a picking "
                                                   "manually with this operation type. If it is empty, it will use the default location."

class Purchase(models.Model):
    _inherit = "purchase.order"

    def _get_destination_location(self):
        self.ensure_one()
        if not self.custom_dest_location_id:
            return super(Purchase, self)._get_destination_location()
        return self.custom_dest_location_id.id

    custom_dest_location_id = fields.Many2one('stock.location', 'Custom Destination Location', check_company=True,
                                              help="This is the custom destination location when you create a picking "
                                                   "manually with this operation type. If it is empty, it will use the default location.")
