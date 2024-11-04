# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api


class InterCompanyTransferConfigEpt(models.Model):
    """
    Model for Configuration of Inter company Transfers.
    @author: Maulik Barad.
    """
    _name = "inter.company.transfer.config.ept"
    _description = 'Inter Company Transfer Configuration'

    name = fields.Char(help="Name of this Configuration.")
    type = fields.Selection([("ict", "Inter Company"), ("internal", "Internal")], default="ict")
    set_default_flow = fields.Boolean("Set as Default", help="Set this Workflow in ICT record as default.")

    auto_confirm_orders = fields.Boolean("Confirm Orders", help="Automatically confirms the Sale and Purchase order.")
    auto_validate_delivery = fields.Boolean("Validate Delivery", help="Automatically validates Delivery Order.")
    auto_validate_receipt = fields.Boolean("Validate Receipt", help="Automatically validates Receipt.")
    auto_create_invoices = fields.Boolean("Create Invoices", help="Automatically creates invoice for orders.")
    auto_validate_invoices = fields.Boolean("Validate Invoices", help="Automatically validates invoices.")
    create_backorder = fields.Boolean(help="Create Backorder, when stock is not available for the product.")

    # confirm_orders_reverse = fields.Boolean("Confirm Orders for Reverse",
    #                                         help="Automatically confirms the Sale and Purchase order.")
    # validate_delivery_reverse = fields.Boolean("Validate Delivery for Reverse",
    #                                            help="Automatically validates Delivery Order.")
    # validate_receipt_reverse = fields.Boolean("Validate Receipt for Reverse", help="Automatically validates Receipt.")
    create_invoices_reverse = fields.Boolean("Create Credit Notes for Reverse",
                                             help="Automatically creates invoice for orders.")
    validate_invoices_reverse = fields.Boolean("Validate Credit Notes for Reverse",
                                               help="Automatically validates invoices.")
    create_backorder_reverse = fields.Boolean("Create Backorder for Reverse",
                                              help="Create Backorder, when stock is not available for the product.")

    validate_pickings = fields.Boolean("Validate Transfers", help="Automatically validates Transfers.")
    validate_pickings_reverse = fields.Boolean("Validate Transfers for Reverse",
                                               help="Automatically validates Transfers.")

    @api.onchange("auto_confirm_orders")
    def onchange_auto_confirm_orders(self):
        """
        If 'Confirm Orders' is unchecked, then fields for validating pickings and creating invoice will be unchecked.
        @author: Maulik Barad on Date 18-Dec-2020.
        """
        for record in self:
            if not record.auto_confirm_orders:
                record.auto_validate_delivery = False
                record.auto_validate_receipt = False
                record.auto_create_invoices = False

    @api.onchange("auto_validate_delivery", "auto_validate_receipt", "validate_pickings")
    def onchange_validate_pickings(self):
        """
        If 'Validate Delivery' and 'Validate Receipt' is unchecked, then 'Create Backorder' will be unchecked.
        @author: Maulik Barad on Date 18-Dec-2020.
        """
        for record in self:
            if (record.type == "ict" and not record.auto_validate_delivery and not record.auto_validate_receipt) or (
                    record.type == "internal" and not record.validate_pickings):
                record.create_backorder = False

    @api.onchange("auto_create_invoices")
    def onchange_auto_create_invoices(self):
        """
        If 'Create Invoice' is unchecked, the 'Validate Invoice' will be unchecked too.
        @author: Maulik Barad on Date 18-Dec-2020.
        """
        for record in self:
            if not record.auto_create_invoices:
                record.auto_validate_invoices = False

    @api.onchange("validate_pickings_reverse")
    def onchange_reverse_validate_pickings(self):
        """
        If 'Validate Delivery' and 'Validate Receipt' is unchecked, then 'Create Backorder' will be unchecked.
        @author: Maulik Barad on Date 18-Dec-2020.
        """
        for record in self:
            if not record.validate_pickings_reverse:
                record.create_backorder_reverse = False

    @api.onchange("create_invoices_reverse")
    def onchange_create_invoices_reverse(self):
        """
        If 'Create Invoice' is unchecked, the 'Validate Invoice' will be unchecked too.
        @author: Maulik Barad on Date 18-Dec-2020.
        """
        for record in self:
            if not record.create_invoices_reverse:
                record.validate_invoices_reverse = False
