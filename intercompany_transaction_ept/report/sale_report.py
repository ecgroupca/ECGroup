# -*- coding: utf-8 -*-
"""
For inter_company_transfer_ept module.
"""
from odoo import models, fields as field


class SaleReport(models.Model):
    """
    Inherited for adding relation with inter company transfer.
    @author: Maulik Barad on Date 18-Jan-2021.
    """
    _inherit = "sale.report"

    inter_company_transfer_id = field.Many2one('inter.company.transfer.ept', string="ICT",
                                               groups="intercompany_transaction_ept.inter_company_transfer_user_group,"
                                                      "intercompany_transaction_ept."
                                                      "inter_company_transfer_manager_group",
                                               copy=False, help="Reference of ICT.", readonly=True)

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['inter_company_transfer_id'] = "s.inter_company_transfer_id"
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += """, s.inter_company_transfer_id"""
        return res
