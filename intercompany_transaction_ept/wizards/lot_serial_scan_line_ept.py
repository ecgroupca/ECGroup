# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class LotSerialScanLine(models.TransientModel):
    _name = "lot.serial.scan.line.ept"
    _description = "Lot Serial Scan Line"

    product_id = fields.Many2one("product.product")
    quantity = fields.Float()
    lot_serial_ids = fields.Many2many("stock.lot", string="Lot/Serial")
    import_export_products_id = fields.Many2one("import.export.products.ept")
