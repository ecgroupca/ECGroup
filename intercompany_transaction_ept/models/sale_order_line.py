# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    ict_line_id = fields.Many2one("inter.company.transfer.line.ept")
