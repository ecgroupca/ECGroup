# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields

class InterCompanyTransferLogBookEpt(models.Model):
    """
    For managing the Log details of Inter Company and Internal Warehouse Transfers.
    @author: Maulik Barad.
    """
    _name = "inter.company.transfer.log.book.ept"
    _description = "Inter Company Transfer Log Book"
    

class InterCompanyTransferLogLineEpt(models.Model):
    """
    For managing the Log details of Inter Company and Internal Warehouse Transfers.
    @author: Maulik Barad.
    """
    _name = "inter.company.transfer.log.line.ept"
    _description = "Inter Company Transfer Log Line"
    _rec_name = "ict_message"

    operation = fields.Selection([("import", "Import"), ("ict", "ICT"), ("reverse", "Reverse Transfer"),
                                  ("invoice", "Invoice"), ("auto", "Auto Generate ICT/IWT")])
    ict_message = fields.Text(string="Message")
    ict_log_type = fields.Selection([("error", "Error"), ("mismatch", "Mismatch"), ("info", "Info")], string="Log Type")
    inter_company_transfer_id = fields.Many2one("inter.company.transfer.ept", string="Transfer", store=True)

    def post_log_line(self, message, ict, operation, log_type="error"):
        """
        Creates log line.
        @param operation: Line for which operation.
        @param ict: record of ICT.
        @author: Maulik Barad.
        @param message: Reason of the log.
        @param log_type: Type of the log.
        """
        self.create({
            "ict_message": message,
            "ict_log_type": log_type,
            "operation": operation,
            "inter_company_transfer_id": ict.id if ict else False
        })
