# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

from odoo import api, fields, models, _


class ProductionCancelReason(models.Model):
    _name = "production.cancel.reason"
    _description = "Reasons to cancel the manufaturing order."
    _order = "sequence asc"

    name = fields.Char(string="Reason", required=True)
    sequence = fields.Integer(string="Sequence", required=True)
