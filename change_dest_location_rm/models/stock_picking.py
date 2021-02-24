# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange('custom_dest_location_id')
    def _set_delivery_dest(self):
        for sale in self:
            import pdb;pdb.set_trace()
            if sale.custom_dest_location_id:
                for pick in sale.picking_ids:
                    pick.location_dest_id = sale.custom_dest_location_id
                    if pick.x_custom_dest_loc:
                      pick.location_dest_id = pick.x_custom_dest_loc
                      for line in pick.move_lines:
                         line.location_dest_id = pick.x_custom_dest_loc

    custom_dest_location_id = fields.Many2one('stock.location', 'Custom Destination Location', check_company=True,
                                              help="This is the custom destination location when you create a picking "
                                                   "manually with this operation type. If it is empty, it will use the default location.")
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