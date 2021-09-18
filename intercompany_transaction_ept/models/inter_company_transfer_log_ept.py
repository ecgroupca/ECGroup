"""
For inter_company_transfer_ept module.
"""
from datetime import datetime

from odoo import models, fields, api


class InterCompanyTransferLogBookEpt(models.Model):
    """
    For managing the Logs of Inter Company and Internal Warehouse Transfers.
    @author: Maulik Barad on Date 24-Sep-2019.
    """
    _name = "inter.company.transfer.log.book.ept"
    _description = "Inter Company Transfer Log Book"

    name = fields.Char(string="Name", copy=False)
    ict_log_date = fields.Datetime(string="Log Date", copy=False)
    ict_process = fields.Selection([("inter.company.transfer.ept", "Inter Company Transfer")],
                                   string="Application")
    operation = fields.Selection([("import", "Import"), ("reverse", "Reverse ICT"), ("invoice", "Invoice")])
    inter_company_transfer_id = fields.Many2one("inter.company.transfer.ept")
    ict_log_line_ids = fields.One2many("inter.company.transfer.log.line.ept", "ict_log_id")

    @api.model
    def return_log_record(self, record, operation_type):
        """
        Creates a new log book.
        @author: Maulik Barad on Date 09-Oct-2019.
        """
        record_name = 'LOG/' + record._name + '/' + str(record.id)
        sequence_id = self.env.ref('intercompany_transaction_ept.inter_company_process_log_seq').ids
        if sequence_id:
            record_name = self.env['ir.sequence'].browse(sequence_id).next_by_id()
        log_vals = {
            'name':record_name,
            'ict_log_date':datetime.now(),
            'ict_process':record._name,
            'operation':operation_type,
            'inter_company_transfer_id':record.id
            }
        return self.create(log_vals)

    def post_log_line(self, message, log_type='error'):
        """
        Creates log line for log book.
        @author: Maulik Barad on Date 09-Oct-2019.
        @param message: Reason of the log.
        @param log_type: Type of the log.
        """
        log_line_vals = {
            'ict_message':message,
            'ict_log_type': log_type,
            'ict_log_id': self.id,
        }
        self.env['inter.company.transfer.log.line.ept'].create(log_line_vals)
        return True


class InterCompanyTransferLogLineEpt(models.Model):
    """
    For managing the Log details of Inter Company and Internal Warehouse Transfers.
    @author: Maulik Barad on Date 24-Sep-2019.
    """
    _name = "inter.company.transfer.log.line.ept"
    _description = 'Inter Company Transfer Log Line Process'

    ict_message = fields.Text(string="Message")
    ict_log_type = fields.Selection([('error', 'Error'),
                                     ('mismatch', 'Mismatch'),
                                     ('info', 'Info')], string="Log Type")
    ict_log_id = fields.Many2one('inter.company.transfer.log.book.ept', string="ICT Process Log",
                                 ondelete='cascade')
