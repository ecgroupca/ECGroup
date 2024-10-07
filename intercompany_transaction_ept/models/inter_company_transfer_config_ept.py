# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
   
                                       
import logging

from datetime import datetime
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger("ict_ept")


class InterCompanyTransferEpt(models.Model):
    """
    For managing the Inter Company and Internal Warehouse Transfers.
    @author: Maulik Barad.
    """
    _name = "inter.company.transfer.ept"
    _description = "Inter Company Transfer EPT"
    _order = "id desc"
    _inherit = ["barcodes.barcode_events_mixin", "mail.thread", "mail.activity.mixin"]

    def _default_auto_workflow(self):
        """
        This method used to set default workflow for the ict record.
        @author: Maulik Barad on Date 22-Dec-2020.
        """
        default_workflow = self.env["inter.company.transfer.config.ept"].search(
            [("set_default_flow", "=", True), ("type", "=", self._context.get("default_type"))], limit=1)
        return default_workflow

    name = fields.Char(help="Name of Inter company transfer.")

    source_warehouse_id = fields.Many2one("stock.warehouse", string="From Warehouse",
                                          help="Source warehouse to transfer stock from.")
    source_company_id = fields.Many2one(related="source_warehouse_id.company_id", string="From Company", store=True,
                                        help="Company of Source warehouse.")
    destination_warehouse_id = fields.Many2one("stock.warehouse", string="To Warehouse",
                                               help="Destination warehouse to transfer stock to.")
    destination_company_id = fields.Many2one(related="destination_warehouse_id.company_id", string="To Company",
                                             store=True, help="Company of Destination warehouse.")

    inter_company_transfer_line_ids = fields.One2many("inter.company.transfer.line.ept", "inter_company_transfer_id",
                                                      string="Transfer Lines", help="ICT Lines", copy=True)

    state = fields.Selection([("draft", "Draft"), ("processed", "Processed"), ("cancel", "Cancelled")], copy=False,
                             default="draft", help="State of ICT.", tracking=True)
    type = fields.Selection([("ict", "ICT"), ("ict_reverse", "Reverse ICT"), ("internal", "Internal"),
                             ("int_reverse", "Reverse Internal")], default="ict",
                            help="The type of Transfer.")

    log_line_ids = fields.One2many("inter.company.transfer.log.line.ept", "inter_company_transfer_id",
                                   string="Inter Company Log Lines", help="Logs of ICT.")
    log_count = fields.Integer(compute="_compute_log_line_ids", help="Count of Logs.")
    message = fields.Char(copy=False, help="Message for ICT.")
    processed_date = fields.Datetime(copy=False, help="Date when ICT is processed.")
    crm_team_id = fields.Many2one("crm.team", string="Sales Team",
                                  default=lambda self: self.env["crm.team"]._get_default_team_id(),
                                  help="Sales team")
    pricelist_id = fields.Many2one("product.pricelist", help="Pricelist for prices of Products.")
    currency_id = fields.Many2one(related="pricelist_id.currency_id", help="Currency of company or by pricelist.")
    group_id = fields.Many2one("procurement.group", string="Procurement Group", copy=False)
    auto_workflow_id = fields.Many2one("inter.company.transfer.config.ept", default=_default_auto_workflow,
                                       ondelete="restrict")

    inter_company_transfer_id = fields.Many2one("inter.company.transfer.ept", string="ICT", copy=False)
    reverse_inter_company_transfer_ids = fields.One2many("inter.company.transfer.ept", "inter_company_transfer_id",
                                                         string="Reverse ICT", copy=False,
                                                         help="Reverse ICTs generated from current ICT.")

    sale_order_ids = fields.One2many("sale.order", "inter_company_transfer_id", copy=False,
                                     help="Sale orders created by the ICT.")
    purchase_order_ids = fields.One2many("purchase.order", "inter_company_transfer_id", copy=False,
                                         help="Purchase orders created by the ICT.")
    picking_ids = fields.One2many("stock.picking", "inter_company_transfer_id", copy=False,
                                  help="Pickings created by the ICT.")
    invoice_ids = fields.One2many("account.move", "inter_company_transfer_id", copy=False,
                                  help="Invoices and Vendor bills created by the ICT.")

    _sql_constraints = [("source_destination_warehouse_unique",
                         "CHECK(source_warehouse_id != destination_warehouse_id)",
                         "Source and Destination warehouse must be different!")]

    @api.depends("log_line_ids")
    def _compute_log_line_ids(self):
        """
        Counts Log line records of ICT.
        @author: Maulik Barad.
        """
        for ict in self:
            ict.log_count = len(ict.log_line_ids)

    def on_barcode_scanned(self, barcode):
        """
        This method handles Barcode scanning.
        @author: Maulik Barad.
        @param barcode: Scanned barcode.
        """
        ict_line_obj = self.env["inter.company.transfer.line.ept"]

        product_id = self.env["product.product"].search(["|", ("barcode", "=", barcode),
                                                         ("default_code", "=", barcode)], limit=1)
        if not product_id:
            return {"warning": {"title": _("Warning"),
                                "message": _("Product Not Found"),
                                "type": "notification"}}

        line = ict_line_obj.search([("inter_company_transfer_id", "=", self._origin.id),
                                    ("product_id", "=", product_id.id)], limit=1)
        if line:
            line.write({"quantity": line.quantity + 1})
        else:
            ict_line_obj.create({"inter_company_transfer_id": self._origin.id,
                                 "product_id": product_id.id, "quantity": 1})
        return True

    @api.onchange("source_warehouse_id")
    def onchange_source_warehouse_id(self):
        """
        Method will be executed when the value of source warehouse will be changed.
        @author: Maulik Barad.
        @return: Domain for destination warehouse.
        """
        if not self.source_warehouse_id:
            self.destination_warehouse_id = False
        if self.source_warehouse_id == self.destination_warehouse_id:
            self.destination_warehouse_id = False
        self.currency_id = self.source_company_id.currency_id

        # If it's not internal type then the both warehouses should have different companies.
        domain_operator = "="
        if self.type != "internal":
            domain_operator = "!="
        else:
            if self.source_company_id != self.destination_company_id:
                self.destination_warehouse_id = False
        return {"domain": {"destination_warehouse_id": [("company_id", domain_operator, self.source_company_id.id),
                                                        ("id", "!=", self.source_warehouse_id.id)]}}

    @api.onchange("destination_warehouse_id")
    def onchange_destination_warehouse_id(self):
        """
        Method will be executed when the value of destination warehouse will be changed.
        @author: Maulik Barad.
        """
        if not self.destination_warehouse_id:
            return

        self.pricelist_id = self.destination_company_id.partner_id.with_company(
            self.source_company_id).property_product_pricelist

        self.crm_team_id = self.destination_company_id.partner_id.with_company(
            self.source_company_id).team_id or self.crm_team_id

        return

    @api.onchange("pricelist_id")
    def onchange_pricelist_id(self):
        """
        If pricelist is changed, this method will call default_price_get for changing price in ict lines.
        @author: Maulik Barad.
        """
        for record in self:
            record.inter_company_transfer_line_ids.default_price_get()

    @api.model_create_multi
    def create(self, vals_list):
        """
        Inherited Method for giving sequence to ICT.
        @author: Maulik Barad.
        @param vals_list: List of values.
        """
        for vals in vals_list:
            record_name = "New"
            sequence_id = False
            if vals.get("type", "") in ["ict", ""]:
                sequence_id = self.env.ref("intercompany_transaction_ept.ir_sequence_inter_company_transaction").ids
            elif vals.get("type", "") == "ict_reverse":
                sequence_id = self.env.ref(
                    "intercompany_transaction_ept.ir_sequence_reverse_inter_company_transaction").ids
            elif vals.get("type", "") == "internal":
                sequence_id = self.env.ref("intercompany_transaction_ept.ir_sequence_internal_transfer").ids
            elif vals.get("type", "") == "int_reverse":
                sequence_id = self.env.ref("intercompany_transaction_ept.ir_sequence_reverse_internal_transaction").ids
            if sequence_id:
                record_name = self.env["ir.sequence"].browse(sequence_id).next_by_id()
            vals.update({"name": record_name})
        res = super(InterCompanyTransferEpt, self).create(vals_list)
        return res                                                                   