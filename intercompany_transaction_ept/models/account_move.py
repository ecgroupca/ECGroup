"""
For inter_company_transfer_ept module.
"""
from odoo import models, fields, api


class AccountMove(models.Model):
    """
    Inherited for adding relation with inter company transfer.
    @author: Maulik Barad on Date 24-Sep-2019.
    """
    _inherit = 'account.move'

    inter_company_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT",
                                                copy=False, help="Reference of ICT.")
