# -*- coding: utf-8 -*-
"""
For inter_company_transfer_ept module.
"""
from odoo import models, fields


class SaleReport(models.Model):
    """
    Inherited for adding relation with inter company transfer.
    Added by Udit Ramani on 18th December 2019
    """
    _inherit = "sale.report"

    inter_company_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT",
                                                copy=False, help="Reference of ICT.", readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['inter_company_transfer_id'] = ", s.inter_company_transfer_id as inter_company_transfer_id"
        groupby += ', s.inter_company_transfer_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
