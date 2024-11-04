# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class AccountMove(models.Model):
    """
    Inherited for adding relation with inter company transfer.
    @author: Maulik Barad.
    """
    _inherit = 'account.move'

    inter_company_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT", copy=False,
                                                help="Reference of ICT.")
