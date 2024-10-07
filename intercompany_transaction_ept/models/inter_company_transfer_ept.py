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

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        """
        Inherited for removing create functionality from reverse ICT view.
        @author: Maulik Barad.
        @change: Changed method name from fields_view_get to get_view in v16.
        """
        context = self._context
        res = super(InterCompanyTransferEpt, self).get_view(view_id=view_id, view_type=view_type, **options)
                                                                                       
                                                                                                    
        doc = etree.XML(res["arch"])
        if view_type in ["form", "tree"]:
            if context.get("default_type", "ict_reverse") in ["ict_reverse", "int_reverse"]:
                for node in doc.xpath("//tree"):
                    node.set("create", "false")
                for node in doc.xpath("//form"):
                    node.set("create", "false")
            res["arch"] = etree.tostring(doc)
        return res

    def action_cancel(self):
        """
        Cancels an ict.
        @author: Maulik Barad.
        """
        pickings = self.picking_ids
        invoices = self.invoice_ids
        if self.state == "processed":
            if pickings.filtered(lambda x: x.state == "done"):
                raise UserError(_("You can not cancel Inter Company Transfer which has done pickings."))
                                          
            if invoices.filtered(lambda x: x.state == "post"):
                raise UserError(_("You can not cancel Inter Company Transfer which has posted invoices."))
                                          
            self.sale_order_ids.with_context(disable_cancel_warning=True).action_cancel()
            self.purchase_order_ids.button_cancel()
            pickings.action_cancel()
            invoices.button_cancel()
        self.write({"state": "cancel", "message": "ICT has been cancelled by %s" % self.env.user.name})
                                 

    def process_ict(self):
        """
        This method creates Sale and Purchase orders or the Internal pickings. Then process as per the Workflow
        Configuration.
        @author: Maulik Barad on Date 18-Jan-2021.
        """
        context = self._context.copy() or {}
        if context.get("default_type"):
            context.pop("default_type")

        # clean the default_inter_company_transfer_id record from the context because while create account move
        # from stock move at that time it set the ict record in journal entry due to default value of ict record.
        if context.get("default_inter_company_transfer_id"):
            context.pop("default_inter_company_transfer_id")

        for record in self:
            if record.with_context(context).check_user_validation():
                if not record.inter_company_transfer_line_ids:
                    msg = _("Please Add Products to Process the ICT record.")
                    raise ValidationError(msg)

                transfer_type = record.type
                # Processing the Inter Warehouse Transfer and Reverse of it.
                _logger.info("Processing the %s." % record.name)
                if transfer_type in ["internal", "int_reverse"]:
                    internal_transfers = record.create_internal_transfer_ept()
                    if internal_transfers:
                        if ((record.type == "internal" and record.auto_workflow_id.validate_pickings) or (
                                record.type == "int_reverse" and record.auto_workflow_id.validate_pickings_reverse)):
                            record.validate_ict_pickings(internal_transfers)
                    else:
                        continue

                # Processing the Reverse ICT.
                elif transfer_type == "ict_reverse":
                    processed = record.with_context(context).process_reverse_ict()
                    if not processed:
                        continue

                # Processing the ICT.
                else:
                    record.with_company(record.source_company_id).create_ict_sale_order()
                    record.with_company(record.destination_company_id).create_ict_purchase_order()
                    _logger.info("Sale and Purchase orders are created for %s." % record.name)

                    record.with_context(context).process_ict_by_workflow()
                                                                   
                                                                
                                               
                                                                                          
                                                                 
                                               

                _logger.info("%s is processed." % record.name)
                record.write({"state": "processed", "processed_date": datetime.today(),
                              "message": "Transfer is processed successfully by %s" % self.env.user.name})

        return True

    def create_internal_transfer_ept(self):
        """
        Creates Internal Transfers for same Company's Warehouses.
        @author: Maulik Barad.
        """
        self.ensure_one()
        procurement_group_obj = self.env["procurement.group"]
        procurements = []

        destination_warehouse = self.destination_warehouse_id

                                                                   
                                                                                                    
                        
                                                                        

                                
                                                             
                                                              
                                                                  

        group_id, route_ids = self.get_group_and_route(destination_warehouse)
                                                                                                
                                                            
                                                    
                                                                                              

        if not group_id:
            return False
        # Prepares list of tuples for procurement.
        for line in self.inter_company_transfer_line_ids:
            procurements.append(
                procurement_group_obj.Procurement(line.product_id, line.quantity, line.product_id.uom_id,
                                                                       
                                                  destination_warehouse.lot_stock_id, self.name, False,
                                                  destination_warehouse.company_id,
                                                  values={"warehouse_id": destination_warehouse,
                                                          "route_ids": route_ids[0] if route_ids else [],
                                                          "group_id": self.group_id}))

        if procurements:
            procurement_group_obj.run(procurements)

        pickings = self.env["stock.picking"].search([("group_id", "=", group_id.id)])
        if not pickings:
            raise UserError(_("No Pickings are created for this record."))
                                                                                  
                                                   
        pickings.write({"inter_company_transfer_id": self.id})
                                                  
                                    
        picking = pickings.filtered(lambda x: x.location_id.id == self.source_warehouse_id.lot_stock_id.id)
        if picking:
            picking.action_assign()
        return pickings

    def get_group_and_route(self, destination_warehouse):
        """
        This method is used to create a procurement group and finding routes for the inter warehouse transfer.
        @param destination_warehouse: Record of the Warehouse.
        @author: Maulik Barad on Date 31-Dec-2020.
        """
        group_id = self.env["procurement.group"].create({"name": self.name,
                                                         "partner_id": destination_warehouse.partner_id.id})
        if not group_id:
            raise UserError(_("Problem with creation of procurement group."))
        self.group_id = group_id

        route_ids = self.env["stock.route"].search([("supplied_wh_id", "=", destination_warehouse.id),
                                                    ("supplier_wh_id", "=", self.source_warehouse_id.id)])
        if not route_ids:
            msg = "No routes are found.\nPlease configure warehouse routes and set in products."
            if self._context.get("auto_process"):
                self.env["inter.company.transfer.log.line.ept"].post_log_line(msg, self, "reverse", "info")
                return False, False
            raise ValidationError(_(msg))

        return group_id, route_ids

    def create_ict_sale_order(self):
        """
        Creates sale order for ICT of different companies.
        @author: Maulik Barad on Date 23-Dec-2020.
                                         
        """
        log_line_obj = self.env["inter.company.transfer.log.line.ept"]
        sale_order_lines = []
        sale_obj = self.env["sale.order"]
        dropship_route = self.env.ref("stock_dropshipping.route_drop_shipping", False)

        for record in self:
            _logger.info("Creating Sale Order for %s." % record.name)
            order_vals = record.prepare_ict_sale_order_vals()

            for line in record.inter_company_transfer_line_ids:
                if dropship_route and dropship_route in line.product_id.route_ids:
                    message = "Dropship Product can not be transferred via Intercompany Transfer. Product: %s" % \
                              line.product_id.name
                    log_line_obj.post_log_line(message, self, "ict", "mismatch")
                    continue
                line_vals = record.prepare_ict_sale_order_line_vals(line)
                sale_order_lines += [(0, 0, line_vals)]
                                                          

            if sale_order_lines:
                order_vals.update({"order_line": sale_order_lines, "inter_company_transfer_id": record.id})
                sale_order = sale_obj.create(order_vals)
                sale_order.order_line._compute_tax_id()
                _logger.info("%s is created." % sale_order.name)

        return True
                                                               
                                                                              
                                                                                   

    def prepare_ict_sale_order_vals(self):
        """
        This method prepares dictionary to create sale order with assigning values from ICT and calling necessary
        onchange methods.
        @author: Maulik Barad on Date 23-Dec-2020.
        """
        sale_obj = self.env["sale.order"]
        customer_partner_id = self.destination_company_id.partner_id

        new_order = sale_obj.new({"partner_id": customer_partner_id.id,
                                  "warehouse_id": self.source_warehouse_id.id,
                                  "pricelist_id": self.pricelist_id.id,
                                  "company_id": self.source_company_id.id})
        # new_order.onchange_partner_id()
        # new_order.onchange_partner_shipping_id()
        if self.crm_team_id:
            new_order.team_id = self.crm_team_id.id

        return new_order._convert_to_write(new_order._cache)

    def prepare_ict_sale_order_line_vals(self, line):
        """
        This method prepares dictionary to create sale order line.
        @param line: Record of ICT line.
        @param order_id: Id of the sale order.
        @author: Maulik Barad on Date 23-Dec-2020.
        """
        new_so_line = self.env["sale.order.line"].new({"product_id": line.product_id})

        # Assigns custom values and calls necessary on_change methods.
        # new_so_line.product_id_change()
        new_so_line.update({"product_uom_qty": line.quantity, "price_unit": line.price, "ict_line_id": line.id})

        return new_so_line._convert_to_write(new_so_line._cache)

    def create_ict_purchase_order(self):
        """
        Creates purchase order for ICT of different companies.
        @author: Maulik Barad on Date 23-Dec-2020.
                                             
        """
        log_line_obj = self.env["inter.company.transfer.log.line.ept"]
        purchase_order_lines = []
        purchase_obj = self.env["purchase.order"]
        dropship_route = self.env.ref("stock_dropshipping.route_drop_shipping", False)

        for record in self:
            _logger.info("Creating Purchase Order for %s." % record.name)

                                     
                                                                               
                                                                                               
                                                                                
                                            
                                                          
            order_vals = record.prepare_ict_purchase_order_vals()
                                                                                                 

                                           
            for line in record.inter_company_transfer_line_ids:
                if dropship_route and dropship_route in line.product_id.route_ids:
                    message = "Dropship Product can not be transferred via Intercompany Transfer. Product: %s" % \
                              line.product_id.name
                    log_line_obj.post_log_line(message, self, "ict", "mismatch")
                    continue
                line_vals = record.prepare_ict_purchase_order_line_vals(line)
                purchase_order_lines += [(0, 0, line_vals)]

            if purchase_order_lines:
                                               
                order_vals.update({"order_line": purchase_order_lines, "inter_company_transfer_id": record.id})
                purchase_order = purchase_obj.create(order_vals)
                purchase_order._compute_tax_id()
                _logger.info("%s is created." % purchase_order.name)

        return True

    def prepare_ict_purchase_order_vals(self):
        """
        This method prepares dictionary to create purchase order with assigning values from ICT and calling necessary
        onchange methods.
        @author: Maulik Barad on Date 23-Dec-2020.
        """
        new_order = self.env["purchase.order"].new({"currency_id": self.currency_id.id,
                                                    "partner_id": self.source_company_id.partner_id.id,
                                                    "company_id": self.destination_company_id.id})
        new_order.onchange_partner_id()

        new_order.currency_id = self.currency_id.id
        new_order.picking_type_id = self.destination_warehouse_id.in_type_id

        return new_order._convert_to_write(new_order._cache)

    def prepare_ict_purchase_order_line_vals(self, line):
        """
        This method prepares dictionary to create purchase order line.
        @param line: Record of ICT line.
        @author: Maulik Barad on Date 23-Dec-2020.
        """
        new_po_line = self.env["purchase.order.line"].new({"product_id": line.product_id,
                                                           "currency_id": self.currency_id,
                                                           "company_id": self.destination_company_id.id,
                                                           "date_order": fields.Datetime.now()})

        # Assigns custom values and calls necessary on_change methods.
        new_po_line.onchange_product_id()
        new_po_line.update({"product_qty": line.quantity,
                            "price_unit": line.price,
                            "product_uom": line.product_id.uom_id.id,
                            "ict_line_id": line.id})

        return new_po_line._convert_to_write(new_po_line._cache)

    def process_ict_by_workflow(self):
        """
        This method process the ict record as per passed parameters.
        @author: Maulik Barad on Date 30-Dec-2020.
                                                            
                                                    
        """
        self.ensure_one()
        auto_workflow = self.auto_workflow_id
        _logger.info("Processing the %s with %s workflow." % (self.name, auto_workflow.name))
        if auto_workflow.auto_confirm_orders:
            self.confirm_orders()
            _logger.info("Orders are confirmed for %s." % self.name)

            if auto_workflow.auto_validate_delivery or auto_workflow.auto_validate_receipt:
                self.auto_validate_ict_pickings()
                _logger.info("Pickings are validated for %s." % self.name)
                                                                                

            if auto_workflow.auto_create_invoices:
                self.create_ict_invoices()
                _logger.info("Invoices are created for %s." % self.name)
                if auto_workflow.auto_validate_invoices and self.invoice_ids:
                    self.invoice_ids.action_post()
                    _logger.info("Invoices are posted for %s." % self.name)
        return True

    def confirm_orders(self):
        """
        Confirms sale and purchase orders of ict.
        @author: Maulik Barad on Date 23-Dec-2020.
        """
        for record in self:
            sale_orders = record.sale_order_ids.filtered(lambda x: x.state in ["draft", "sent"])
            sale_orders.write({"origin": record.name or ""})
            sale_orders.with_company(record.source_company_id).action_confirm()
                                                                                        

            purchase_orders = record.purchase_order_ids.filtered(lambda x: x.state in ["draft", "sent"])
            purchase_orders.write({"origin": record.name or ""})
            purchase_orders.with_company(record.destination_company_id).button_confirm()
                           
                                     
                                                                                  
                                                                       
                                
                                                                          

        return True
                                                           
                    
                                                                                    
                                          
                                                      
                            
                                                        
                                                             
                           
                                                                                    
                                                                          

    def auto_validate_ict_pickings(self):
        """
        This method filters pickings as per configuration and validates them via validate_ict_picking method.
        @author: Maulik Barad in Date 23-Dec-2020.
        """
        pickings = self.env["stock.picking"]
        if self.auto_workflow_id.auto_validate_delivery:
            pickings += self.picking_ids.filtered(lambda x: x.location_dest_id.usage == "customer")
        if self.auto_workflow_id.auto_validate_receipt:
            vendor_picking = self.picking_ids.filtered(lambda x: x.location_id.usage == "supplier")
            moves = vendor_picking.move_ids
            if moves.move_dest_ids:
                moves = self.get_destination_moves(moves)
            pickings += moves.picking_id
        _logger.info("Validating pickings for %s." % self.name)
        self.validate_ict_pickings(pickings)
        return True

    def get_destination_moves(self, moves):
        """
        This method will give the most destination moves of passed moves.
        @author: Maulik Barad on Date 19-Feb-2021.
        """
        return_filter = False
        if self.type == "ict_reverse":
            return_filter = True
        if moves.move_dest_ids:
            dest_ids = moves.move_dest_ids
            if return_filter:
                dest_ids -= moves.returned_move_ids
            if dest_ids:
                moves = self.get_destination_moves(dest_ids)
        return moves

    def validate_ict_pickings(self, pickings):
        """
        This method is used to validate the pickings of ICT as per configuration.
        @param pickings: Records of the picking to validate.
        @author: Maulik Barad in Date 23-Dec-2020.
        """
        for picking in pickings.filtered(lambda x: x.state not in ["cancel", "done"]):
            _logger.info("Validating %s for %s." % (picking.name, self.name))
            skip_backorder = False
            picking_ids_not_to_backorder = []
            if picking.state == "done":
                continue
            if picking.state != "assigned":
                if picking.move_ids.move_orig_ids:
                    completed = self.validate_ict_pickings(
                        picking.move_ids.move_orig_ids.picking_id.sorted(lambda x: x.id))
                    if not completed:
                        return False
                picking.action_assign()
                if picking.state != "assigned":
                    continue

            if (self.type in ["ict", "internal"] and not self.auto_workflow_id.create_backorder) or (
                    self.type in ["ict_reverse", "int_reverse"] and not self.auto_workflow_id.create_backorder_reverse):
                skip_backorder = True
                picking_ids_not_to_backorder = picking.id

            result = picking.with_context(skip_sms=True, skip_backorder=skip_backorder,
                                          picking_ids_not_to_backorder=picking_ids_not_to_backorder).button_validate()
            if isinstance(result, dict):
                result = self.process_immediate_and_backorder_transfer(result)
                if isinstance(result, dict):  # For handling Immediate and Backorder both cases
                    self.process_immediate_and_backorder_transfer(result)
            if picking.state == "done":
                picking.message_post(body=_("Picking is done by Auto workflow of ICT."))
                _logger.info("%s is validated." % picking.name)
        return True

    def process_immediate_and_backorder_transfer(self, result):
        """
        This method will handle the immediate transfers and backorder confirmation.
        @param result: Response from the button validate method.
        @author: Maulik Barad on Date 29-Dec-2020.
        """
        context = result.get("context")
        model = result.get("res_model", "")
        result = False
        # model can be stock.immediate.transfer or stock.backorder.confirmation
        if model in ["stock.immediate.transfer", "stock.backorder.confirmation"]:
            record = self.env[model].with_context(context, skip_sms=True).create({})
            result = record.process()
        return result

    def create_ict_invoices(self):
        """
        Creates invoice and vendor bill for sale and purchase order respectively.
        @author: Maulik Barad on Date 23-Dec-2020.
        """
        for record in self:
            _logger.info("Creating invoices for %s." % record.name)
            sale_order = record.sale_order_ids.filtered(
                lambda x: x.state in ["sale", "done"] and not x.invoice_ids.filtered(
                    lambda i: i.type == "out_invoice" and i.state in ["draft", "posted"]))
            if sale_order.order_line.filtered(lambda x: x.qty_to_invoice):
                sale_order.with_company(record.source_company_id)._create_invoices()

            purchase_order = record.purchase_order_ids.filtered(
                lambda x: x.state in ["purchase", "done"] and not x.invoice_ids.filtered(
                    lambda i: i.type == "in_invoice" and i.state in ["draft", "posted"]))
            if purchase_order.order_line.filtered(lambda x: x.qty_to_invoice):
                purchase_order.with_company(record.destination_company_id).action_create_invoice()

        return True

    def create_reverse_ict(self):
        """
        Creates reverse.inter.company.transfer.ept model's record and opens it's in wizard.
        @author: Maulik Barad.
        @return: Action for opening the reverse ict's wizard.
        """
        reverse_ict_line_obj = self.env["reverse.inter.company.transfer.line.ept"]
        reverse_line_vals = []

                                                                                          
                                                                                               

        # reverse_type = "ict_reverse" if self.type == "ict" else "int_reverse"
        # inter_company_transfer_ids = self.search([("inter_company_transfer_id", "=", self.id),
        #                                           ("type", "=", reverse_type),
        #                                           ("state", "!=", "cancel")])
        for line in self.inter_company_transfer_line_ids:
            if line.delivered_qty != 0.0 and line.delivered_qty <= line.quantity:
                vals = self.prepare_reverse_ict_line_vals(line)
                if isinstance(vals, dict) and vals.get("quantity"):
                                                                                       
                                                                                     

                                                                                     
                                              
                                       
                                            
                                                          
                                                                                          
                                                                           
                                                                        
                                                                           
                                           
                    reverse_line_vals.append(vals)
                                                         
                                                                                          
                                                                                          
                else:
                    msg = "Dropship Product is skipped in Reverse ICT as it can not be transferred via Intercompany " \
                          "Transfer. Product: %s" % line.product_id.name
                    self.env["inter.company.transfer.log.line.ept"].post_log_line(msg, self, "reverse", "mismatch")
                                                                                           
            else:
                msg = """Line is not considered as there is no product is delivered yet. Product : %s""" % \
                      line.product_id.name
                self.env["inter.company.transfer.log.line.ept"].post_log_line(msg, self, "reverse", "info")

        reverse_ict_lines = reverse_ict_line_obj.create(reverse_line_vals)
                                    

        # Opens wizard if reverse lines are found.
        if reverse_ict_lines:
            return {
                "type": "ir.actions.act_window",
                "res_model": "reverse.inter.company.transfer.ept",
                "views": [(False, "form")],
                "context": {"default_inter_company_transfer_id": self.id,
                            "default_reverse_ict_line_ids": [(6, 0, reverse_ict_lines.ids)]},
                "target": "new",
            }
        raise UserError(_("There are no products found for the Reverse Transaction!!"))

    def prepare_reverse_ict_line_vals(self, line):
        """
        This method is used to prepare dictionary for creating the reverse ict lines.
        @param line: Record of ict line.
        @param ict_ids: Other reverse ICTs for same ICT.
        @author: Maulik Barad on Date 30-Dec-2020.
        """
        dropship_route = self.env.ref("stock_dropshipping.route_drop_shipping", False)
        if dropship_route and dropship_route in line.product_id.route_ids:
            return False
        line_vals = {"product_id": line.product_id.id, "price": line.price,
                     "delivered_qty": line.delivered_qty}
        # If already reverse ICTs are there, then quantity will be decreased.
        if line.lot_serial_ids:
            if self.type != "internal":
                lot_serial_ids = self.get_destination_lots_for_reverse(line)
            else:
                lot_serial_ids = line.lot_serial_ids
            line_vals.update({"lot_serial_ids": lot_serial_ids})

        # if ict_ids:
        #     total_qty_delivered = 0.0
        #     for ict in ict_ids:
        #         for transfer_line in ict.inter_company_transfer_line_ids.filtered(
        #                 lambda x: x.product_id == line.product_id):
        #             total_qty_delivered += transfer_line.quantity
        #     delivered_qty = line.delivered_qty - total_qty_delivered
        #     if delivered_qty > 0.0:
        #         line_vals.update({"quantity": delivered_qty})
        # else:
        line_vals.update({"quantity": line.delivered_qty})
        return line_vals

    def get_destination_lots_for_reverse(self, line):
        """
        This method searches for the lot/serial numbers in destination company, when the ict is reversing.
        @param lot_serials: Records of the lots of the ict line.
        @author: Maulik Barad on Date 30-Dec-2020.
        """
        lot_serial_ids = self.env["stock.lot"].search([("name", "in", line.lot_serial_ids.mapped("name")),
                                                       ("product_id", "=", line.product_id.id),
                                                       ("company_id", "=", self.destination_company_id.id)])
        return lot_serial_ids

    def process_reverse_ict(self):
        """
        Processes reverse ICT created from ICT.
        @author: Maulik Barad on Date 19-Feb-2021.
        """
        outgoing_picking = False
        picking_ids_to_validate = []
        processed = False

        if self.inter_company_transfer_id.sale_order_ids:
            outgoing_picking = self.inter_company_transfer_id.picking_ids.filtered(
                lambda x: x.picking_type_id.code == "outgoing" and x.state == "done")

        if outgoing_picking:
            moves = self.get_destination_moves(outgoing_picking.move_ids)
            picking_ids_to_validate += self.generate_return_pickings(moves.picking_id, [])[0]
            if picking_ids_to_validate:
                pickings = outgoing_picking.browse(picking_ids_to_validate).sorted(lambda x: x.id)
                # pickings.write({"inter_company_transfer_id": self.id})
                self.process_reverse_ict_by_workflow(pickings)
                processed = True
                                                                                                 
                                                                                                                      
                            
                                                                                    

        return processed
                                                                 
                                                                                                    
                                                                                                   
                                                                               
                                                                                                                         

    def generate_return_pickings(self, picking, returned_pickings):
        """
        This method is used to create return pickings for the All pickings.
        @param picking: Picking to create return for.
        @param returned_pickings: Already returned pickings.
        @author: Maulik Barad on Date 19-Feb-2021.
        """
        picking_ids = []
        stock_return_picking_obj = self.env["stock.return.picking"]

        for done_picking in picking.filtered(lambda x: x.state == "done" and x not in returned_pickings):
            move_vals = []
            return_picking_wizard = stock_return_picking_obj.create({"picking_id": done_picking.id})
                                                           
                                                                                         
                                                                           
                                                             
                                                                 
                                                           
                                                             

            if return_picking_wizard.picking_id:
                                       
                                                                                 
                                                                                     
                                                                                   
                                                                            
                                                                                      
                return_picking_wizard._onchange_picking_id()
                return_picking_wizard.product_return_moves.unlink()
                                                                          
                                                                                                   
                                                                            
                                
                                                                    
                                
                                         

                                                                                     
                reverse_ict_lines = self.inter_company_transfer_line_ids
                for reverse_line in reverse_ict_lines:
                    move_vals += self.prepare_return_move_vals(reverse_line, done_picking)
                           
                        

                # for return_move in return_picking_wizard.product_return_moves:
                #     reverse_line = reverse_ict_lines.filtered(lambda x: x.product_id == return_move.product_id)
                #     if len(reverse_line) > 1:
                #         reverse_line = reverse_line.filtered(
                #             lambda x: return_move.move_id.move_line_ids.lot_id in x.lot_serial_ids)
                #     if reverse_line:
                #         return_move.quantity = reverse_line.quantity

                if move_vals:
                    return_picking_wizard.product_return_moves = move_vals
                    picking_action = return_picking_wizard.with_context(default_ict=self.id).create_returns()
                    picking_ids.append(picking_action.get("res_id"))
                    returned_pickings.append(done_picking)
                    if done_picking.move_ids.move_orig_ids:
                        # For skipping the Partial Returned moves.
                        moves_for_return = done_picking.move_ids.move_orig_ids.filtered(
                            lambda x: x.origin_returned_move_id not in done_picking.move_ids)
                        # For skipping Return of the Make to Order pickings.
                        moves_for_return = moves_for_return.filtered(
                            lambda x: not (x.picking_id.sale_id and x.picking_id.location_dest_id ==
                                           done_picking.picking_type_id.warehouse_id.lot_stock_id))
                        pickings, already_returned = self.generate_return_pickings(moves_for_return.picking_id,
                                                                                   returned_pickings)
                        picking_ids += pickings
                        returned_pickings += already_returned

        return picking_ids, returned_pickings

    def process_reverse_ict_by_workflow(self, pickings):
        """
        This method is used to process reverse ICT.
        @param pickings: Pickings to validate if configured in Workflow.
        @author: Maulik Barad on Date 19-Feb-2021.
        """
        auto_workflow = self.auto_workflow_id
        if auto_workflow.validate_pickings_reverse:
            self.validate_ict_pickings(pickings)
        if auto_workflow.create_invoices_reverse:
            self.reverse_invoices()
            if auto_workflow.validate_invoices_reverse and self.invoice_ids:
                list(map(lambda x: x.action_post(), self.invoice_ids))
                # Got singleton error from Indian Accounting
                # self.invoice_ids.action_post()

    def reverse_invoices(self):
        """
        This method is used to generate the Credit Notes for Invoices.
        @author: Maulik Barad on Date 19-Feb-2021.
        """
        account_move_reversal_obj = reverse_moves = self.env["account.move.reversal"]
        invoices = self.inter_company_transfer_id.invoice_ids.filtered(lambda x: x.state == "posted")
        context = {"active_model": "account.move"}

        for invoice in invoices:
            reverse_move = account_move_reversal_obj.with_context(context, active_ids=invoice.ids,
                                                                  default_journal_id=invoice.journal_id.id).create({})
            reverse_move.reverse_moves()
                                                               
                                                  
                                                                                          
                                                                                  
                                                                                             
                                                                                   

            for invoice_line in reverse_move.new_move_ids.invoice_line_ids:
                                                                                    
                                                                           
                                                                                       
                                                      
                                                                                      
                              
                                                                  
                                                                    
                match_line = self.inter_company_transfer_line_ids.filtered(
                    lambda x: x.product_id == invoice_line.product_id)
                if match_line:
                                                       
                    invoice_line.with_context(check_move_validity=False).write({
                        "quantity": sum(match_line.mapped("quantity")), "price_unit": match_line.price
                    })
                                                                                        
                                                   
                                                

            # reverse_move.new_move_ids.with_context(check_move_validity=False)._recompute_dynamic_lines()
            reverse_moves += reverse_move

            reverse_moves.new_move_ids.with_context(check_move_validity=False).write(
                {"inter_company_transfer_id": self.id})

        return True

    def prepare_return_move_vals(self, ict_line, picking):
        """
        This method is used to prepare vals for return move based on Product Type.
        @param ict_line: Record of the Reverse ICT line.
        @param picking: Record of picking to be reversed.
        @author: Maulik Barad on Date 24-Feb-2021.
        """
        move_vals = []
        product = ict_line.product_id
        bom_point_dict = self.check_bom_product(product)
        if product in bom_point_dict:
            move_vals += self.prepare_return_move_vals_for_bom(ict_line, bom_point_dict, picking)
        else:
            move = picking.move_ids.filtered(lambda x: x.product_id == product and x.state == "done")
            if ict_line.lot_serial_ids:
                lot_serial_list = ict_line.lot_serial_ids.mapped("name")
                move = move.filtered(lambda x: any([move_line.lot_id.name in lot_serial_list for move_line in
                                                    x.move_line_ids]))
            if not move:
                return move_vals
            quantity = ict_line.quantity
            if move.product_uom_qty < quantity:
                quantity = move.product_uom_qty
            move_vals.append((0, 0, {"product_id": move.product_id.id,
                                     "move_id": move.id,
                                     "quantity": quantity,
                                     "uom_id": move.product_id.uom_id.id,
                                     "to_refund": True}))
        return move_vals

    def prepare_return_move_vals_for_bom(self, ict_line, bom_point_dict, picking):
        """
        This method explodes the BoM and prepares the return move vals for that.
        @author: Maulik Barad on Date 24-Feb-2021.
        """
        move_vals = []
        bom_product = ict_line.product_id

        bom_point = bom_point_dict[bom_product]
        from_uom = bom_product.uom_id
        to_uom = bom_point.product_uom_id
        factor = from_uom._compute_quantity(1, to_uom) / bom_point.product_qty
        bom, lines = bom_point.explode(bom_product, factor, picking_type=bom_point.picking_type_id)

        for line in lines:
            product = line[0].product_id
            move = picking.move_ids.filtered(lambda x: x.product_id == product and x.state == "done")
            quantity = ict_line.quantity
            if move.product_uom_qty < quantity:
                quantity = move.product_uom_qty
            product_qty = line[1].get("qty", 0) * quantity
            product_uom = line[0].product_uom_id
            move_vals.append((0, 0, {"product_id": product.id,
                                     "move_id": move.id,
                                     "quantity": product_qty,
                                     "uom_id": product_uom.id,
                                     "to_refund": True}))

        return move_vals

    def check_bom_product(self, product):
        """
        Checks for the Product, if it is of BoM type.
        @author: Maulik Barad on Date 24-Feb-2021.
        """
        bom_point_dict = {}
        mrp_module = self.env["ir.module.module"].sudo().search([("name", "=", "mrp"), ("state", "=", "installed")])

        if mrp_module:
            bom_point_dict = self.env["mrp.bom"].sudo()._bom_find(products=product, bom_type="phantom")
        return bom_point_dict

    def check_user_validation(self):
        """
        Checks for ICT User configuration and the company.
        @author: Maulik Barad.
        """
        for record in self:
            if record.source_warehouse_id.company_id not in self.env.user.company_ids:
                if record.source_warehouse_id.company_id not in self.env.user.company_id.child_ids:
                                                                                               
                    raise ValidationError(_("""User '%s' can not process this Inter Company Transfer.\n User from
                    Source Warehouse Company can Process it !!!!\n\nPlease Process it with User of Source Warehouse
                    Company.""") % self.env.user.name)
        return True

                                          
           
                                                           
                                                  
                                                               
                                      
           
                
                                                                  
                                              
                                             
                                 
                                    
             
                   

    def reset_to_draft(self):
        """
        Changes state to draft.
        @author: Maulik Barad.
        """
        for record in self:
            record.state = "draft"
        return True

    def unlink(self):
        """
        Inherited method for preventing the deletion of ICT.
        @author: Maulik Barad.
        """
        for record in self:
            if record.state == "processed":
                raise UserError(_("You can not delete transaction, which is in Processed state !!"))
        return super(InterCompanyTransferEpt, self).unlink()

    def open_related_records(self):
        """
        Returns action for opening the records of the Sale order, Purchase order, Pickings, Invoices and Log Book.
        Need to pass the model in the Context to specify the records.
        @author: Maulik Barad on Date 10-Mar-2021.
        @return: Action to open related records as per the model passed in the Context.
        """
        record_ids = []
        name = self.name

        context = self.env.context.copy()
        res_model = self._context.get("view_model")

        if res_model == "inter.company.transfer.ept":
            name = "Reverse ICTs"
            record_ids = self.reverse_inter_company_transfer_ids.ids
        elif res_model == "sale.order":
            name = "Sales Orders"
            record_ids = self.sale_order_ids.ids
        elif res_model == "purchase.order":
            name = "Purchase Orders"
            record_ids = self.purchase_order_ids.ids
        elif res_model == "stock.picking":
            name = "Pickings"
            record_ids = self.picking_ids.ids
        elif res_model == "account.move":
            name = "Invoices"
            record_ids = self.invoice_ids.ids
            context.update({"group_by": "move_type"})
        elif res_model == "inter.company.transfer.log.line.ept":
            name = "Logs"
            record_ids = self.log_line_ids.ids

        if record_ids:
            action = {
                "name": name,
                "type": "ir.actions.act_window",
                "res_model": res_model,
                "context": context
            }
            if len(record_ids) == 1:
                action.update({"res_id": record_ids[0], "views": [(False, "form")]})
            else:
                action.update({"domain": [("id", "in", record_ids)], "views": [(False, "tree"), (False, "form")]})
            return action
        return True

    def open_lot_serial_scan_wizard(self):
        """
        Returns action for opening the lot serial scan wizard.
        @author: Maulik Barad on Date 06-Jan-2021.
        """
        form_view = self.env.ref("intercompany_transaction_ept.import_product_lot_scan_form_view", False)
        if form_view:
            form_view = form_view.id

        context = dict(self._context)
        context.update({"default_lot_company_id": self.source_company_id.id})
        if context.get("loose_lot"):
            context.update({"default_loose_lot_transfer": True})
        return {
            "name": "Scan Lot/Serial",
            "type": "ir.actions.act_window",
            "res_model": "import.export.products.ept",
            "context": context,
            "views": [(form_view, "form")],
            "target": "new"
        }