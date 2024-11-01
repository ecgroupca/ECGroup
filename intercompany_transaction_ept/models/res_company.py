"""
For inter_company_transfer_ept module.
"""
from odoo import fields, models


class ResCompany(models.Model):
    """
    Inherited for adding configuration for inter company transfers.
    @author: Maulik Barad on Date 24-Sep-2019.
    """
    _inherit = "res.company"

    sale_journal_id = fields.Many2one('account.journal', check_company=True,
                                      help="Sale Journal for creating invoice on.")
    purchase_journal_id = fields.Many2one('account.journal', check_company=True,
                                          help="Purchase Journal for creating vendor bill on.")
