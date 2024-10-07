"""
For inter_company_transfer_ept module.
"""
from odoo import models, fields, _, api
from odoo.exceptions import Warning


class InterCompanyTransferConfigEpt(models.Model):
    """
    Model for Configuration of Inter company Transfers.
    @author: Maulik Barad on Date 24-Sep-2019.
    """
    _name = "inter.company.transfer.config.ept"
    _rec_name = "sequence_id"
    _description = 'Inter Company Transfer Configuration'

    sequence_id = fields.Many2one('ir.sequence', help="Sequence")
    auto_confirm_orders = fields.Boolean(help="Automatically confirms the Sale and Purchase order.")
    auto_create_invoices = fields.Boolean(help="Automatically creates invoice for orders.")
    auto_validate_invoices = fields.Boolean(help="Automatically validates invoices.")
    description = fields.Char(help="Description for this configuration.")
    refund_method = fields.Selection([('refund', 'Create a draft credit note'),
                                      ('cancel', 'Cancel: create credit note and reconcile')],
                                     default='refund', string="Refund Method",
                                     help="Refund base on this type. You can not Modify and"
                                     "Cancel if the invoice is already reconciled")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id,
                                 readonly=True)

    @api.model
    def post_check_ict(self):
        """
        Cron Method for post checking the ICTs if processed as current ICT configurations.
        @author: Maulik Barad on Date 21-Oct-2019.
        """
        configuration = self.search([])
        ict_records = self.env['inter.company.transfer.ept'].search([('state', '=', 'processed'),
                                                                     ('type', '=', 'ict')])
        if configuration.auto_confirm_orders:
            not_confirmed_icts = ict_records.filtered(
                lambda x: x.sale_order_ids.filtered(lambda x: x.state in ['draft', 'sent']) or
                x.purchase_order_ids.filtered(lambda x: x.state in ['draft', 'sent']))
            not_confirmed_icts.confirm_orders()

        if configuration.auto_create_invoices:
            ict_without_invoices = ict_records.filtered(
                lambda x: x.invoice_ids == x.invoice_ids.filtered(lambda x: x.state == 'cancel') or not x.invoice_ids
                )
            ict_without_invoices.create_invoice()

            if configuration.auto_validate_invoices:
                not_validated_icts = ict_records.filtered(lambda x: x.invoice_ids.filtered(lambda x: x.state == 'draft'))

                not_validated_icts -= ict_without_invoices
                for ict in not_validated_icts:
                    ict.invoice_ids.filtered(lambda x: x.type == 'out_invoice' and x.state != 'cancel').action_post()
                    ict.invoice_ids.filtered(lambda x: x.type == 'in_invoice' and x.state != 'cancel').action_post()
        return True