# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import models, fields, api
_logger = logging.getLogger(__name__)

class MRPProduction(models.Model):
    """MRP"""

    _inherit = 'mrp.production'
    
    location_id = fields.Many2one(readonly=False)
    location_dest_id = fields.Many2one(readonly=False)              